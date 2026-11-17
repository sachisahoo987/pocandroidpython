"""Run local Android BDD tests with managed Appium and device lifecycle."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

LOGGER = logging.getLogger("local_android_runner")
DEFAULT_APPIUM_URL = "http://127.0.0.1:4723"
DEFAULT_APP_PACKAGE = "com.androidsample.generalstore"
STARTUP_TIMEOUT_SECONDS = 120


class RunnerError(RuntimeError):
    """A local Android run could not be prepared or cleaned up."""


def _setting(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def _run_adb(adb: str, device: str, *arguments: str) -> str:
    result = subprocess.run(
        [adb, "-s", device, *arguments],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RunnerError(f"ADB command failed ({' '.join(arguments)}): {detail}")
    return result.stdout.strip()


def _resolve_device(adb: str, requested: str | None) -> str:
    result = subprocess.run(
        [adb, "devices"],
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if result.returncode:
        raise RunnerError(f"Unable to list Android devices: {result.stderr.strip()}")

    online = [
        line.split()[0]
        for line in result.stdout.splitlines()[1:]
        if len(line.split()) >= 2 and line.split()[1] == "device"
    ]
    if requested:
        if requested not in online:
            raise RunnerError(
                f"Configured Android device {requested!r} is not online. "
                f"Online devices: {', '.join(online) or 'none'}."
            )
        return requested
    if len(online) == 1:
        return online[0]
    if not online:
        raise RunnerError("No online Android device found. Connect an emulator/device and enable ADB.")
    raise RunnerError(
        f"Multiple Android devices are online ({', '.join(online)}); set UDID to select one."
    )


def _resolve_activity(adb: str, device: str, package: str) -> str:
    package_paths = _run_adb(adb, device, "shell", "pm", "path", package)
    if not package_paths.startswith("package:"):
        raise RunnerError(f"App package {package!r} is not installed on {device}.")

    resolution = _run_adb(
        adb, device, "shell", "cmd", "package", "resolve-activity", "--brief", package
    )
    components = re.findall(r"(?m)^([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)\s*$", resolution)
    if not components:
        raise RunnerError(
            f"Unable to resolve a launch activity for {package!r}: {resolution or 'no result'}"
        )
    component_package, activity = components[-1].split("/", maxsplit=1)
    if component_package != package:
        raise RunnerError(
            f"Resolved activity belongs to unexpected package {component_package!r}."
        )
    return activity


def _requested_runtime_permissions(package_dump: str, permission_list: str) -> list[str]:
    lines = package_dump.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == "requested permissions:")
    except StopIteration:
        return []

    requested: set[str] = set()
    for line in lines[start + 1 :]:
        entry = line.strip()
        if entry.endswith(" permissions:"):
            break
        if re.fullmatch(r"[A-Za-z0-9_.]+", entry):
            requested.add(entry)
    dangerous = set(re.findall(r"(?m)^\s*permission:([A-Za-z0-9_.]+)\s*$", permission_list))
    return sorted(requested & dangerous)


def _grant_runtime_permissions(adb: str, device: str, package: str) -> list[str]:
    if _setting("AUTO_GRANT_PERMISSIONS", "true").casefold() not in {
        "true",
        "1",
        "yes",
        "on",
    }:
        LOGGER.info("Automatic Android runtime permission grants are disabled.")
        return []

    package_dump = _run_adb(adb, device, "shell", "dumpsys", "package", package)
    dangerous_permissions = _run_adb(adb, device, "shell", "pm", "list", "permissions", "-g", "-d")
    permissions = _requested_runtime_permissions(package_dump, dangerous_permissions)
    granted: list[str] = []
    for permission in permissions:
        if re.search(
            rf"(?m)^\s*{re.escape(permission)}:\s+granted=true\b", package_dump
        ):
            continue
        _run_adb(adb, device, "shell", "pm", "grant", package, permission)
        granted.append(permission)
    if granted:
        LOGGER.info("Granted requested Android runtime permission(s): %s", ", ".join(granted))
    else:
        LOGGER.info("No missing requested Android runtime permissions.")
    return granted


def _reset_app_data(adb: str, device: str, package: str) -> None:
    if _setting("RESET_APP_DATA", "true").casefold() not in {"true", "1", "yes", "on"}:
        LOGGER.info("Preserving existing app data for this run.")
        return
    result = _run_adb(adb, device, "shell", "pm", "clear", package)
    if result.casefold() != "success":
        raise RunnerError(f"Android did not confirm clearing app data for {package!r}: {result}")
    LOGGER.info("Reset app data for a clean scenario start.")


def _appium_endpoint(url: str) -> tuple[str, int, str, str]:
    parsed = urlsplit(url.rstrip("/"))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RunnerError(f"APPIUM_URL must be an HTTP(S) URL; received {url!r}.")
    path = parsed.path
    if path.casefold().endswith("/wd/hub"):
        path = path[:-7].rstrip("/")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise RunnerError(f"Invalid port in APPIUM_URL {url!r}.") from exc
    endpoint = urlunsplit((parsed.scheme, parsed.netloc, path, "", "")).rstrip("/")
    status_url = f"{endpoint}/status"
    return parsed.hostname, port, path, status_url


def _server_ready(status_url: str) -> bool:
    try:
        with urlopen(status_url, timeout=2) as response:
            status = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, HTTPError, URLError):
        return False
    return bool(status.get("value", {}).get("ready"))


def _appium_main() -> Path:
    configured = os.environ.get("APPIUM_MAIN", "").strip()
    if configured:
        path = Path(configured).expanduser().resolve()
        if path.is_file():
            return path
        raise RunnerError(f"APPIUM_MAIN does not exist: {path}")

    command = shutil.which("appium.cmd") or shutil.which("appium")
    if command:
        npm_package = Path(command).resolve().parent / "node_modules" / "appium"
        for candidate in (npm_package / "index.js", npm_package / "build" / "lib" / "main.js"):
            if candidate.is_file():
                return candidate

    npm = shutil.which("npm")
    if npm:
        result = subprocess.run(
            [npm, "root", "-g"],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            npm_package = Path(result.stdout.strip()) / "appium"
            for candidate in (npm_package / "index.js", npm_package / "build" / "lib" / "main.js"):
                if candidate.is_file():
                    return candidate
    raise RunnerError(
        "Appium CLI was not found. Install Appium and the UiAutomator2 driver, "
        "or set APPIUM_MAIN to Appium's JavaScript entry point."
    )


def _tail(path: Path, lines: int = 35) -> str:
    try:
        return "".join(path.read_text(encoding="utf-8", errors="replace").splitlines(True)[-lines:])
    except OSError:
        return ""


class ManagedAppiumServer:
    def __init__(self, status_url: str, host: str, port: int, base_path: str):
        self.status_url = status_url
        self.host = host
        self.port = port
        self.base_path = base_path
        self.process: subprocess.Popen[bytes] | None = None
        self.log_path = Path(tempfile.gettempdir()) / "pocandroid-appium-server.log"
        self._log_file: BinaryIO | None = None

    def start_if_needed(self) -> bool:
        if _server_ready(self.status_url):
            LOGGER.info("Using the already-running Appium server at %s", self.status_url)
            return False

        node = shutil.which("node")
        if not node:
            raise RunnerError("Node.js is required to start Appium but was not found on PATH.")
        main = _appium_main()
        self._log_file = self.log_path.open("wb")
        arguments = [node, str(main), "--address", self.host, "--port", str(self.port)]
        if self.base_path:
            arguments.extend(["--base-path", self.base_path])
        self.process = subprocess.Popen(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
        )

        timeout = int(_setting("APPIUM_STARTUP_TIMEOUT", str(STARTUP_TIMEOUT_SECONDS)))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _server_ready(self.status_url):
                LOGGER.info("Started Appium (PID %s); log: %s", self.process.pid, self.log_path)
                return True
            if self.process.poll() is not None:
                details = _tail(self.log_path)
                raise RunnerError(
                    f"Appium exited during startup with code {self.process.returncode}. "
                    f"Log: {self.log_path}\n{details}"
                )
            time.sleep(0.5)
        details = _tail(self.log_path)
        raise RunnerError(
            f"Appium did not become ready within {timeout} seconds. "
            f"Log: {self.log_path}\n{details}"
        )

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            LOGGER.info("Stopping managed Appium server (PID %s).", self.process.pid)
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                LOGGER.warning("Appium did not stop gracefully; terminating its managed process.")
                self.process.kill()
                self.process.wait(timeout=5)
        if self._log_file is not None:
            self._log_file.close()


def main(arguments: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        LOGGER.info("python-dotenv is unavailable; using process environment only.")

    try:
        adb = shutil.which("adb")
        if not adb:
            raise RunnerError("ADB was not found on PATH. Install Android platform-tools.")

        device = _resolve_device(adb, os.environ.get("UDID", "").strip() or None)
        package = _setting("APP_PACKAGE", DEFAULT_APP_PACKAGE)
        activity = os.environ.get("APP_ACTIVITY", "").strip()
        if not activity:
            activity = _resolve_activity(adb, device, package)
        else:
            _run_adb(adb, device, "shell", "pm", "path", package)

        os.environ.update(
            {
                "RUN_ENV": "local",
                "PLATFORM": "android",
                "DEVICE_NAME": _setting("DEVICE_NAME", device),
                "UDID": device,
                "APP_PACKAGE": package,
                "APP_ACTIVITY": activity,
                "AUTO_GRANT_PERMISSIONS": _setting("AUTO_GRANT_PERMISSIONS", "true"),
                "NO_RESET": _setting("NO_RESET", "true"),
                "RECORD_VIDEO": _setting("RECORD_VIDEO", "false"),
                "ACTION_SCREENSHOTS": _setting("ACTION_SCREENSHOTS", "false"),
            }
        )
        LOGGER.info("Using Android device %s and app %s/%s.", device, package, activity)
        _reset_app_data(adb, device, package)
        _grant_runtime_permissions(adb, device, package)

        appium_url = _setting("APPIUM_URL", DEFAULT_APPIUM_URL)
        host, port, base_path, status_url = _appium_endpoint(appium_url)
        server = ManagedAppiumServer(status_url, host, port, base_path)
        server_started = False
        try:
            server_started = server.start_if_needed()
            test_arguments = arguments if arguments is not None else sys.argv[1:]
            if not test_arguments:
                test_arguments = ["tests/bdd"]
            report_directory = Path(tempfile.gettempdir()) / "pocandroid-allure-results"
            report_directory.mkdir(parents=True, exist_ok=True)
            pytest_arguments = [
                "-p",
                "no:cacheprovider",
                f"--alluredir={report_directory}",
                *test_arguments,
            ]
            return subprocess.call([sys.executable, "-m", "pytest", *pytest_arguments])
        finally:
            server.stop()
            if server_started:
                LOGGER.info("Managed Appium server has stopped.")
    except (RunnerError, OSError, subprocess.SubprocessError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
