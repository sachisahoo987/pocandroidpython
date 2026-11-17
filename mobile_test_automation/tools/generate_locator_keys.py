"""Generate Python Enum modules from the existing page/locator JSON resource."""

from __future__ import annotations

import argparse
import json
import keyword
import re
import sys
from pathlib import Path
from typing import Any

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_INPUT = (
    _REPOSITORY_ROOT / "mobile_test_automation" / "resources" / "locators" / "locators.json"
)
_DEFAULT_OUTPUT = _REPOSITORY_ROOT / "mobile_test_automation" / "generated" / "keys"
_PAGE_NAMES = {
    "FormPage": "FORMPAGE",
    "ProductPage": "PRODUCTPAGE",
    "CartPage": "CARTPAGE",
}


def _class_name(page_name: str) -> str:
    """Preserve the locator schema's page-name capitalization."""
    return f"{page_name[0].upper()}{page_name[1:]}Key"


def _constant_name(locator_key: str) -> str:
    """Mirror the source generator's separator/camel-case normalization."""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", locator_key.strip())
    normalized = re.sub(r"([a-z])([A-Z])", r"\1_\2", normalized).upper()
    if not normalized or not normalized.isidentifier() or keyword.iskeyword(normalized):
        raise ValueError(
            f"Locator key cannot be represented as a Python enum member: {locator_key!r}"
        )
    return normalized


def _load_pages(input_path: Path) -> list[tuple[str, str, list[tuple[str, str]]]]:
    try:
        root: Any = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Unable to read locator JSON file: {input_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid locator JSON in {input_path} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(root, dict):
        raise ValueError(f"Locator JSON root must be a JSON object: {input_path}")
    if type(root.get("$schemaVersion")) is not int or root["$schemaVersion"] != 1:
        raise ValueError(f"Unsupported or missing locator schema version: {input_path}")

    pages: list[tuple[str, str, list[tuple[str, str]]]] = []
    for page_name, raw_locators in root.items():
        if page_name == "$schemaVersion":
            continue
        if page_name not in _PAGE_NAMES:
            raise ValueError(f"Unknown page: {page_name}")
        if not isinstance(raw_locators, dict):
            raise ValueError(f"Locator page {page_name!r} must contain a JSON object.")

        members: list[tuple[str, str]] = []
        seen_members: set[str] = set()
        for locator_key in raw_locators:
            if not isinstance(locator_key, str):
                raise ValueError(f"Locator keys for page {page_name!r} must be strings.")
            locator = raw_locators[locator_key]
            if (
                not isinstance(locator, dict)
                or set(locator) != {"xpath"}
                or not isinstance(locator.get("xpath"), dict)
                or set(locator["xpath"]) != {"android", "ios"}
                or any(
                    value is not None and (not isinstance(value, str) or not value.strip())
                    for value in locator["xpath"].values()
                )
            ):
                raise ValueError(
                    f"Locator {page_name}.{locator_key} must define Android and iOS XPath values."
                )
            member_name = _constant_name(locator_key)
            if member_name in seen_members:
                raise ValueError(
                    f"Locator keys on page {page_name!r} produce duplicate member {member_name!r}."
                )
            seen_members.add(member_name)
            members.append((member_name, locator_key))
        pages.append((page_name, _class_name(page_name), members))
    return pages


def _render_module(page_name: str, class_name: str, members: list[tuple[str, str]]) -> str:
    lines = [
        '"""Generated locator keys for the existing JSON page resource."""',
        "",
        "from enum import Enum",
        "",
        "",
        f"class {class_name}(str, Enum):",
    ]
    if members:
        lines.extend(f"    {name} = {json.dumps(key, ensure_ascii=True)}" for name, key in members)
    else:
        lines.append("    pass")
    lines.extend(
        [
            "",
            "    @property",
            "    def page(self) -> str:",
            f"        return {json.dumps(page_name)}",
            "",
            "    @property",
            "    def key(self) -> str:",
            "        return self.value",
            "",
        ]
    )
    return "\n".join(lines)


def generate_key_sources(input_path: Path, output_dir: Path) -> list[Path]:
    """Generate one importable Python Enum module per recognized JSON page."""
    pages = _load_pages(Path(input_path))
    rendered = [
        (output_dir / f"{class_name}.py", _render_module(page, class_name, members))
        for page, class_name, members in pages
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Generated locator key modules."""\n', encoding="utf-8")

    for output_path, source in rendered:
        output_path.write_text(source, encoding="utf-8")
    return [path for path, _ in rendered]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Python Enum modules from the shared platform locator JSON."
    )
    parser.add_argument("--input", type=Path, default=_DEFAULT_INPUT, help="Locator JSON path.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Python package directory for generated modules.",
    )
    args = parser.parse_args(argv)
    try:
        generated = generate_key_sources(args.input, args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"Locator key generation failed: {exc}", file=sys.stderr)
        return 1

    for path in generated:
        print(f"Generated: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
