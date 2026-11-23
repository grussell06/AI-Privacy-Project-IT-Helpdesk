from __future__ import annotations

import re
from pathlib import Path

from .models import Match


class Detector:
    STRUCTURED_PATTERNS = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "ASSET": re.compile(r"\bLT-[0-9]{5}\b"),
        "TICKET": re.compile(r"\bINC-[0-9]{4}\b"),
    }

    def __init__(self, names: list[str]) -> None:
        self.names = names

    @classmethod
    def from_file(cls, path: Path) -> Detector:
        return cls([
            line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ])

    def detect(self, text: str) -> list[Match]:
        found: list[Match] = []
        for name in self.names:
            pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)")
            found.extend(Match(m.start(), m.end(), "NAME", m.group()) for m in pattern.finditer(text))
        for category, pattern in self.STRUCTURED_PATTERNS.items():
            found.extend(Match(m.start(), m.end(), category, m.group()) for m in pattern.finditer(text))
        return found


class OverlapResolver:
    PRIORITY = {"EMAIL": 0, "ASSET": 1, "TICKET": 2, "NAME": 3}

    def resolve(self, candidates: list[Match]) -> list[Match]:
        ranked = sorted(candidates, key=lambda m: (-(m.end - m.start), self.PRIORITY.get(m.category, 99), m.start))
        selected: list[Match] = []
        for candidate in ranked:
            if not any(candidate.start < item.end and item.start < candidate.end for item in selected):
                selected.append(candidate)
        return sorted(selected, key=lambda m: m.start)
