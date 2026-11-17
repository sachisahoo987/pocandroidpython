"""Named logging helpers for mobile automation."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger("mobile_automation")


def info(message: str) -> None:
    _LOGGER.info("%s", message)


def warn(message: str) -> None:
    _LOGGER.warning("%s", message)


def error(message: str) -> None:
    _LOGGER.error("%s", message)
