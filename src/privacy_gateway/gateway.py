from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .detection import Detector, OverlapResolver
from .mapping import Masker, RequestMapping
from .models import GatewayError, GatewayResult, Match
from .policy import PolicyEngine
from .provider import MockProvider, Provider, ProviderFailure, ProviderTimeout
from .validation import ResponseValidator, Restorer


class PrivacyGateway:
    def __init__(self, detector: Detector, provider: Provider | None = None,
                 mapping_factory: Callable[[str], RequestMapping] = RequestMapping) -> None:
        self.detector = detector
        self.provider = provider or MockProvider()
        self.mapping_factory = mapping_factory
        self.overlaps = OverlapResolver()
        self.policies = PolicyEngine()
        self.masker = Masker()
        self.validator = ResponseValidator()
        self.restorer = Restorer()

    @classmethod
    def default(cls) -> PrivacyGateway:
        path = Path(__file__).resolve().parents[1] / "data" / "synthetic_names.txt"
        return cls(Detector.from_file(path))

    def process(self, request_id: str, text: str, policies: dict[str, str] | None = None,
                prompt_version: str | None = None) -> GatewayResult:
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", request_id):
            raise GatewayError("INVALID_REQUEST", "request_id has an invalid format")
        if not isinstance(text, str) or not text.strip():
            raise GatewayError("INVALID_REQUEST", "text must be a non-empty string")
        if "[[" in text or "]]" in text:
            raise GatewayError("RESERVED_SYNTAX", "input contains reserved placeholder syntax")
        version = "v2" if prompt_version is None else prompt_version
        if not isinstance(version, str) or version not in {"v1", "v2"}:
            raise GatewayError("INVALID_PROMPT", "prompt_version must be v1 or v2")
        matches = self.overlaps.resolve(self.detector.detect(text))
        decisions = self.policies.resolve(matches, policies)
        mapping = self.mapping_factory(request_id)
        try:
            masked = self.masker.apply(text, decisions, mapping)
            try:
                provider_response = self.provider.summarize(masked, version)
            except ProviderTimeout as exc:
                raise GatewayError("PROVIDER_TIMEOUT", "provider timed out") from exc
            except ProviderFailure as exc:
                raise GatewayError("PROVIDER_ERROR", "provider failed") from exc
            except Exception as exc:
                raise GatewayError("PROVIDER_ERROR", "provider failed") from exc
            validated = self.validator.validate(provider_response, mapping)
            output = self.restorer.restore(validated, mapping)
            return GatewayResult(request_id, masked, validated, output, version)
        finally:
            mapping.close()


__all__ = ["Detector", "GatewayError", "GatewayResult", "Match", "MockProvider", "PrivacyGateway"]
