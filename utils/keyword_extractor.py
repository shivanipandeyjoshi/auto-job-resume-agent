from __future__ import annotations

import re
from typing import Iterable

from utils.text_utils import normalize_words


class KeywordExtractor:
    """Extract simple keyword tokens from text."""

    def __init__(self) -> None:
        self._pattern = re.compile(r"[A-Za-z][A-Za-z0-9+#.:-]*")

    def extract(self, text: str) -> list[str]:
        """Extract meaningful keywords from a text block."""

        words = [token for token in self._pattern.findall(text) if len(token) > 2]
        return normalize_words(words)

    def intersect(self, text: str, keywords: Iterable[str]) -> list[str]:
        """Return matching keywords found in text."""

        extracted = set(self.extract(text))
        desired = set(normalize_words(keywords))
        return sorted(extracted & desired)
