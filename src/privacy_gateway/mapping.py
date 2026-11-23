from __future__ import annotations

import re
import secrets

from .models import GatewayError, Policy, PolicyDecision


class RequestMapping:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.namespace = f"g{secrets.token_hex(6)}"
        self._values: dict[str, str] = {}
        self._tokens: dict[tuple[str, str], str] = {}
        self._counts: dict[str, int] = {}
        self.closed = False

    def _require_open(self) -> None:
        if self.closed:
            raise GatewayError("MAPPING_CLOSED", "request mapping is closed")

    def token_for(self, category: str, value: str) -> str:
        self._require_open()
        key = (category, value)
        if key not in self._tokens:
            self._counts[category] = self._counts.get(category, 0) + 1
            token = f"[[{self.namespace}:{category}:{self._counts[category]}]]"
            self._tokens[key] = token
            self._values[token] = value
        return self._tokens[key]

    def contains(self, token: str) -> bool:
        self._require_open()
        return token in self._values

    def value_for(self, token: str) -> str:
        self._require_open()
        return self._values[token]

    def close(self) -> None:
        self._values.clear()
        self._tokens.clear()
        self._counts.clear()
        self.closed = True

    def __len__(self) -> int:
        return len(self._values)


class Masker:
    def apply(self, text: str, decisions: list[PolicyDecision], mapping: RequestMapping) -> str:
        pieces: list[str] = []
        cursor = 0
        for decision in decisions:
            match = decision.match
            pieces.append(text[cursor:match.start])
            if decision.policy is Policy.MASK:
                pieces.append(mapping.token_for(match.category, match.value))
            cursor = match.end
        pieces.append(text[cursor:])
        result = "".join(pieces)
        lines = []
        for line in result.splitlines() or [result]:
            line = re.sub(r"[ \t]+", " ", line)
            line = re.sub(r"\s+([,.;:!?])", r"\1", line)
            lines.append(line.strip())
        return "\n".join(lines)
