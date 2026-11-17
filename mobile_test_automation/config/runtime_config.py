"""Environment-backed configuration helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping


def runtime_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return non-empty environment values with normalized names."""
    if environ is None:
        environ = os.environ
    return {
        str(key).upper(): value
        for key, value in environ.items()
        if value is not None and value.strip()
    }


def get_setting(
    name: str,
    default: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve an option from the environment, then its default."""
    values = runtime_environment(environ)
    value = values.get(name.upper())
    return value.strip() if value is not None and value.strip() else default


def get_bool(
    name: str,
    default: bool = False,
    *,
    environ: Mapping[str, str] | None = None,
) -> bool:
    value = get_setting(name, None, environ=environ)
    if value is None:
        return default
    normalized = value.casefold()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value (true/false).")


def require_environment_value(name: str, environ: Mapping[str, str] | None = None) -> str:
    """Read a required secret from the environment."""
    source = os.environ if environ is None else environ
    value = source.get(name)
    if value is None or not value.strip():
        raise ValueError(f"Missing required environment variable: {name}")
    return value.strip()


def resolve_environment_token(
    value: str | None,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve a full ``${NAME}`` token from the environment, if supplied."""
    if value is None or not (value.startswith("${") and value.endswith("}")):
        return value
    name = value[2:-1]
    source = os.environ if environ is None else environ
    return source.get(name)
