from __future__ import annotations

import re
from typing import Iterable


def slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug."""

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def normalize_words(values: Iterable[str]) -> list[str]:
    """Normalize a list of words by stripping whitespace and deduplicating."""

    return list(dict.fromkeys(item.strip().lower() for item in values if item and item.strip()))
