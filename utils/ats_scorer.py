from __future__ import annotations

from typing import Iterable

from utils.keyword_extractor import KeywordExtractor


class AtsScorer:
    """Simple ATS keyword coverage scorer."""

    def __init__(self) -> None:
        self.extractor = KeywordExtractor()

    def score(self, text: str, keywords: Iterable[str]) -> int:
        """Score coverage based on keyword hits in text."""

        expected = list(keywords)
        if not expected:
            return 0
        hits = self.extractor.intersect(text, expected)
        return int((len(hits) / len(expected)) * 100)
