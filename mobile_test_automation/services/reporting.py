"""Best-effort screenshot and video reporting helpers."""

from __future__ import annotations

import base64
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def safe_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_")
    return normalized or "scenario"


def attach_bytes(name: str, content: bytes, mime_type: str, extension: str) -> bool:
    if not content:
        return False
    try:
        import allure

        allure.attach(content, name=name, attachment_type=mime_type, extension=extension)
        return True
    except Exception:
        return False


def capture_screenshot(driver: Any, name: str = "Screenshot") -> bytes:
    """Return screenshot bytes and attach them when the Allure plugin is present."""
    try:
        content = driver.get_screenshot_as_png()
        if not isinstance(content, bytes):
            content = bytes(content)
        attach_bytes(name, content, "image/png", "png")
        return content
    except Exception:
        return b""


def capture_dom_snapshot(driver: Any, name: str, output_dir: Path) -> Path | None:
    """Persist the current native hierarchy and attach it to Allure when available."""
    try:
        source = driver.page_source
    except Exception:
        LOGGER.exception("Unable to read the current Appium page source for %s.", name)
        return None
    if not source:
        LOGGER.warning("Appium returned an empty page source for %s.", name)
        return None

    destination = output_dir / f"{safe_name(name)}.xml"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
    except OSError:
        LOGGER.exception("Unable to persist the Appium page source at %s.", destination)
        return None
    attach_bytes(name, source.encode("utf-8"), "application/xml", "xml")
    LOGGER.info("Saved failure DOM snapshot to %s.", destination)
    return destination


def start_video_recording(driver: Any, enabled: bool) -> bool:
    if not enabled:
        return False
    parameters = {
        "maxDurationSec": 1800,
        "bitRate": 800000,
        "videoType": "mp4",
        "resolution": "720x1280",
    }
    try:
        driver.execute_script("mobile: startMediaProjectionRecording", parameters)
        return True
    except Exception:
        return False


def stop_video_recording(
    driver: Any,
    scenario_name: str,
    *,
    enabled: bool,
    output_dir: Path = Path("test-output/videos"),
    attempts: int = 3,
    initial_backoff: float = 1.5,
    settle_delay: float = 1.2,
    sleep: Callable[[float], None] = time.sleep,
) -> Path | None:
    """Stop recording with the legacy retry/backoff behavior and attach the MP4."""
    if not enabled:
        return None

    sleep(settle_delay)
    backoff = initial_backoff
    video_data: str | None = None
    for attempt in range(max(1, attempts)):
        try:
            result = driver.execute_script("mobile: stopMediaProjectionRecording")
            if result is not None:
                candidate = result if isinstance(result, str) else str(result)
                if candidate:
                    video_data = candidate
                    break
        except Exception:
            pass
        if attempt + 1 < attempts:
            sleep(backoff)
            backoff *= 2

    if not video_data:
        attach_bytes(
            "Video",
            b"No video was produced or stopping timed out after retries.",
            "text/plain",
            "txt",
        )
        return None

    try:
        video = base64.b64decode(video_data, validate=True)
        if not video:
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / f"{safe_name(scenario_name)}.mp4"
        destination.write_bytes(video)
        attach_bytes("Execution Video", video, "video/mp4", "mp4")
        return destination
    except (OSError, ValueError):
        attach_bytes(
            "Video Error", b"Unable to decode or save the execution video.", "text/plain", "txt"
        )
        return None
