from __future__ import annotations

import re

from .mapping import RequestMapping
from .models import GatewayError

PLACEHOLDER_PATTERN = re.compile(r"\[\[(?P<request>[A-Za-z0-9_-]+):(?P<category>[A-Z]+):(?P<index>[1-9][0-9]*)\]\]")
RESERVED_PATTERN = re.compile(r"\[\[.*?\]\]")


class ResponseValidator:
    def validate(self, response: object, mapping: RequestMapping) -> str:
        if not isinstance(response, str) or not response.strip():
            raise GatewayError("MALFORMED_RESPONSE", "provider response must be non-empty text")
        normalized = response.replace("\r\n", "\n")
        lines = normalized.splitlines()
        summary_lines = [i for i, line in enumerate(lines) if line.startswith("Summary:")]
        steps_lines = [i for i, line in enumerate(lines) if line == "Suggested steps:"]
        if summary_lines != [0] or len(steps_lines) != 1 or steps_lines[0] <= 0:
            raise GatewayError("MALFORMED_RESPONSE", "provider response has invalid sections")
        if not lines[0][len("Summary:"):].strip():
            raise GatewayError("MALFORMED_RESPONSE", "provider response has empty or missing sections")
        step_lines = lines[steps_lines[0] + 1:]
        if not any(re.match(r"^\d+\.[ \t]+\S", line) for line in step_lines):
            raise GatewayError("MALFORMED_RESPONSE", "provider response must include a non-empty numbered step")
        for token in RESERVED_PATTERN.findall(normalized):
            if PLACEHOLDER_PATTERN.fullmatch(token) is None or not mapping.contains(token):
                raise GatewayError("INVALID_PLACEHOLDER", "provider returned an invalid placeholder")
        remainder = RESERVED_PATTERN.sub("", normalized)
        if "[[" in remainder or "]]" in remainder:
            raise GatewayError("INVALID_PLACEHOLDER", "provider returned malformed placeholder syntax")
        return normalized


class Restorer:
    def restore(self, response: str, mapping: RequestMapping) -> str:
        return PLACEHOLDER_PATTERN.sub(lambda m: mapping.value_for(m.group()), response)
