from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GatewayError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Policy(str, Enum):
    MASK = "MASK"
    REMOVE = "REMOVE"


@dataclass(frozen=True)
class Match:
    start: int
    end: int
    category: str
    value: str


@dataclass(frozen=True)
class PolicyDecision:
    match: Match
    policy: Policy


@dataclass(frozen=True)
class GatewayResult:
    request_id: str
    masked_text: str
    provider_response: str
    output: str
    prompt_version: str
