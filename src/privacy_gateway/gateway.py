"""Core single-request privacy gateway pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(
    r"\[\[(?P<request>[A-Za-z0-9_-]+):(?P<category>[A-Z]+):(?P<index>[1-9][0-9]*)\]\]"
)
RESERVED_PATTERN = re.compile(r"\[\[.*?\]\]")


class GatewayError(Exception):
    """A controlled error that is safe to report to the caller."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    category: str
    value: str


@dataclass(frozen=True)
class GatewayResult:
    request_id: str
    masked_text: str
    provider_response: str
    output: str


class Detector:
    """Detect supported values using a local term list and narrow patterns."""

    STRUCTURED_PATTERNS = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "ASSET": re.compile(r"\bLT-[0-9]{5}\b"),
        "TICKET": re.compile(r"\bINC-[0-9]{4}\b"),
    }

    def __init__(self, names: list[str]) -> None:
        self.names = names

    @classmethod
    def from_file(cls, path: Path) -> Detector:
        names = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        return cls(names)

    def detect(self, text: str) -> list[Match]:
        candidates: list[Match] = []

        for name in self.names:
            pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)")
            candidates.extend(
                Match(found.start(), found.end(), "NAME", found.group(0))
                for found in pattern.finditer(text)
            )

        for category, pattern in self.STRUCTURED_PATTERNS.items():
            candidates.extend(
                Match(found.start(), found.end(), category, found.group(0))
                for found in pattern.finditer(text)
            )

        # Prefer the earliest match, then the longest match at the same position.
        candidates.sort(key=lambda item: (item.start, -(item.end - item.start)))
        selected: list[Match] = []
        for candidate in candidates:
            if any(
                candidate.start < existing.end and existing.start < candidate.end
                for existing in selected
            ):
                continue
            selected.append(candidate)
        return sorted(selected, key=lambda item: item.start)


class Masker:
    """Replace matches and keep the mapping local to one request."""

    def mask(
        self, text: str, matches: list[Match], request_id: str
    ) -> tuple[str, dict[str, str]]:
        value_tokens: dict[tuple[str, str], str] = {}
        mapping: dict[str, str] = {}
        category_counts: dict[str, int] = {}
        pieces: list[str] = []
        cursor = 0

        for match in matches:
            key = (match.category, match.value)
            token = value_tokens.get(key)
            if token is None:
                category_counts[match.category] = category_counts.get(match.category, 0) + 1
                token = (
                    f"[[{request_id}:{match.category}:"
                    f"{category_counts[match.category]}]]"
                )
                value_tokens[key] = token
                mapping[token] = match.value

            pieces.append(text[cursor : match.start])
            pieces.append(token)
            cursor = match.end

        pieces.append(text[cursor:])
        return "".join(pieces), mapping


class MockProvider:
    """Deterministic offline substitute for an external AI provider."""

    def summarize(self, masked_ticket: str) -> str:
        return (
            f"Summary: {masked_ticket}\n"
            "Suggested steps:\n"
            "1. Confirm the reported symptoms and recent changes.\n"
            "2. Check the affected device and relevant connection or account settings."
        )


class ResponseValidator:
    """Accept only placeholders issued for the current request."""

    def validate(self, response: str, mapping: dict[str, str]) -> None:
        candidates = RESERVED_PATTERN.findall(response)
        for candidate in candidates:
            if PLACEHOLDER_PATTERN.fullmatch(candidate) is None:
                raise GatewayError(
                    "INVALID_PLACEHOLDER",
                    f"Provider returned a malformed placeholder: {candidate}",
                )
            if candidate not in mapping:
                raise GatewayError(
                    "INVALID_PLACEHOLDER",
                    f"Provider returned an unknown placeholder: {candidate}",
                )

        remainder = RESERVED_PATTERN.sub("", response)
        if "[[" in remainder or "]]" in remainder:
            raise GatewayError(
                "INVALID_PLACEHOLDER",
                "Provider returned malformed reserved placeholder syntax",
            )


class Restorer:
    """Restore values from the current request's validated mapping."""

    def restore(self, response: str, mapping: dict[str, str]) -> str:
        restored = response
        for token, value in mapping.items():
            restored = restored.replace(token, value)
        return restored


class PrivacyGateway:
    """Coordinate one complete local privacy request."""

    def __init__(self, detector: Detector, provider: MockProvider | None = None) -> None:
        self.detector = detector
        self.masker = Masker()
        self.provider = provider or MockProvider()
        self.validator = ResponseValidator()
        self.restorer = Restorer()

    @classmethod
    def default(cls) -> PrivacyGateway:
        names_path = Path(__file__).resolve().parents[1] / "data" / "synthetic_names.txt"
        return cls(Detector.from_file(names_path))

    def process(self, request_id: str, text: str) -> GatewayResult:
        if not request_id or not re.fullmatch(r"[A-Za-z0-9_-]+", request_id):
            raise GatewayError("INVALID_REQUEST", "request_id has an invalid format")
        if not isinstance(text, str) or not text.strip():
            raise GatewayError("INVALID_REQUEST", "text must be a non-empty string")
        if "[[" in text or "]]" in text:
            raise GatewayError(
                "RESERVED_SYNTAX",
                "Input contains syntax reserved for gateway placeholders",
            )

        matches = self.detector.detect(text)
        masked_text, mapping = self.masker.mask(text, matches, request_id)
        provider_response = self.provider.summarize(masked_text)
        self.validator.validate(provider_response, mapping)
        output = self.restorer.restore(provider_response, mapping)
        return GatewayResult(request_id, masked_text, provider_response, output)
