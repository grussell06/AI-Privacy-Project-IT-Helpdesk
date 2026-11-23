from __future__ import annotations

from .models import GatewayError, Match, Policy, PolicyDecision


class PolicyEngine:
    CATEGORIES = {"NAME", "EMAIL", "ASSET", "TICKET"}

    def resolve(self, matches: list[Match], raw: dict[str, str] | None) -> list[PolicyDecision]:
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise GatewayError("INVALID_POLICY", "policies must be an object")
        parsed: dict[str, Policy] = {}
        for category, value in raw.items():
            if category not in self.CATEGORIES or not isinstance(value, str):
                raise GatewayError("INVALID_POLICY", "policy contains an unsupported category or value")
            try:
                parsed[category] = Policy(value)
            except ValueError as exc:
                raise GatewayError("INVALID_POLICY", f"invalid policy for {category}") from exc
        return [PolicyDecision(match, parsed.get(match.category, Policy.MASK)) for match in matches]
