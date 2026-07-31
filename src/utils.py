"""Helper functions: text cleanup, list parsing, and formatting."""

from __future__ import annotations

import re
from datetime import datetime


def clean_text(value: str | None) -> str:
    """Trim whitespace and collapse excessive blank space from a string."""
    if not value:
        return ""
    text = str(value).strip()
    # Collapse 3+ consecutive newlines down to a maximum of two.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def parse_list(value: str | None) -> list[str]:
    """Split a multi-line or comma/semicolon separated string into clean items.

    Users may enter one item per line, or separate items with commas or
    semicolons. Empty items and surrounding whitespace are removed.
    """
    if not value:
        return []

    text = str(value).strip()
    if not text:
        return []

    # Prefer newline splitting; fall back to comma/semicolon if it is a single line.
    if "\n" in text:
        raw_items = text.splitlines()
    else:
        raw_items = re.split(r"[;,]", text)

    items: list[str] = []
    for item in raw_items:
        cleaned = re.sub(r"^\s*[-*\u2022\d.)]+\s*", "", item).strip()
        if cleaned:
            items.append(cleaned)
    return items


def count_items(value: str | None) -> int:
    """Count the number of discrete items in a multi-line/list style field."""
    return len(parse_list(value))


def to_bullets(items: list[str]) -> str:
    """Render a list of strings as a Markdown bullet list."""
    if not items:
        return "_None provided._"
    return "\n".join(f"- {item}" for item in items)


def to_numbered(items: list[str]) -> str:
    """Render a list of strings as a Markdown numbered list."""
    if not items:
        return "_None provided._"
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def slugify(value: str) -> str:
    """Create a filesystem-safe slug from a string."""
    value = (value or "workflow").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "workflow"


def timestamp() -> str:
    """Return a human-friendly timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def file_timestamp() -> str:
    """Return a filename-safe timestamp."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def has_content(value: str | None) -> bool:
    """Return True when a field contains meaningful text."""
    return bool(clean_text(value))


def first_line(value: str | None, fallback: str = "") -> str:
    """Return the first non-empty line of a field, or a fallback string.

    Safe against whitespace-only input (which would otherwise raise IndexError).
    """
    items = parse_list(value)
    return items[0] if items else fallback
