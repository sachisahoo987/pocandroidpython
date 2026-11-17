"""Load QA or stage BrowserStack settings from a properties file."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path

_PROFILE_DIRECTORY = Path(__file__).resolve().parent / "environments"
_PROFILE_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
_ENVIRONMENT_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}\Z")
_PROFILE_PROPERTIES = frozenset(
    {
        "BROWSERSTACK_USERNAME",
        "BROWSERSTACK_ACCESS_KEY",
        "BROWSERSTACK_ANDROID_DEVICE_NAME",
        "BROWSERSTACK_ANDROID_OS_VERSION",
        "BROWSERSTACK_IOS_DEVICE_NAME",
        "BROWSERSTACK_IOS_OS_VERSION",
        "BROWSERSTACK_PROJECT_NAME",
        "BROWSERSTACK_BUILD_NAME",
    }
)


def _read_properties(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Unable to read environment profile: {path}") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        separator = "=" if "=" in line else ":" if ":" in line else None
        if separator is None:
            raise ValueError(f"Invalid property at {path}:{line_number}; expected KEY=VALUE.")
        key, value = (part.strip() for part in line.split(separator, maxsplit=1))
        if not key or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"Invalid property name at {path}:{line_number}.")
        if key in values:
            raise ValueError(f"Duplicate property {key!r} in {path}:{line_number}.")
        values[key] = value
    return values


def _resolve_profile_value(key: str, value: str, environ: Mapping[str, str]) -> str:
    reference = _ENVIRONMENT_REFERENCE.fullmatch(value)
    if not reference:
        if "${" in value or "}" in value:
            raise ValueError(f"Profile property {key} must use a complete ${{VARIABLE}} reference.")
        return value

    variable = reference.group(1)
    resolved = environ.get(variable)
    if resolved is None or not resolved.strip():
        raise ValueError(f"Profile property {key} requires environment variable {variable}.")
    if "\n" in resolved or "\r" in resolved:
        raise ValueError(f"Environment variable {variable} cannot contain newlines.")
    return resolved.strip()


def load_environment_profile(
    environment: str,
    *,
    environ: Mapping[str, str] | None = None,
    profile_directory: Path | None = None,
) -> dict[str, str]:
    """Load one named profile, resolving secret references without logging values."""
    if not _PROFILE_NAME_PATTERN.fullmatch(environment):
        raise ValueError("TEST_ENVIRONMENT must be a valid profile name.")
    profile_name = environment.casefold()
    if profile_name not in {"qa", "stage"}:
        raise ValueError("TEST_ENVIRONMENT must be either qa or stage.")

    source = os.environ if environ is None else environ
    directory = profile_directory or _PROFILE_DIRECTORY
    properties = _read_properties(directory / f"{profile_name}.properties")
    unexpected = set(properties) - _PROFILE_PROPERTIES
    if unexpected:
        raise ValueError(
            "Unsupported environment profile setting(s): " + ", ".join(sorted(unexpected)) + "."
        )
    profile_values = {
        key: _resolve_profile_value(key, value, source) for key, value in properties.items()
    }

    # Explicit workflow inputs override profile defaults and secret references.
    configured = dict(profile_values)
    configured.update(
        {key: value.strip() for key, value in source.items() if value is not None and value.strip()}
    )
    return configured


def configure_github_environment(environment_file: Path, values: Mapping[str, str]) -> None:
    """Persist resolved profile values to the current Actions job without logging them."""
    try:
        with environment_file.open("a", encoding="utf-8", newline="\n") as output:
            for key, value in values.items():
                delimiter = f"__PROFILE_{os.urandom(16).hex()}__"
                if delimiter in value:
                    raise ValueError(
                        f"Profile value for {key} conflicts with the Actions environment delimiter."
                    )
                output.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
    except OSError as exc:
        raise ValueError(
            f"Unable to configure the GitHub Actions environment from {environment_file}."
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load the selected QA or stage BrowserStack properties profile."
    )
    parser.add_argument(
        "--github-env-file",
        type=Path,
        help="GitHub Actions environment file to configure for subsequent steps.",
    )
    args = parser.parse_args(argv)
    try:
        environment = os.environ.get("TEST_ENVIRONMENT", "")
        values = load_environment_profile(environment)
        if args.github_env_file:
            profile_keys = _read_properties(
                _PROFILE_DIRECTORY / f"{environment.casefold()}.properties"
            )
            configure_github_environment(
                args.github_env_file,
                {key: values[key] for key in profile_keys},
            )
    except ValueError as exc:
        print(f"Environment profile configuration failed: {exc}", file=sys.stderr)
        return 1

    print(f"Loaded {environment.casefold()} environment profile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
