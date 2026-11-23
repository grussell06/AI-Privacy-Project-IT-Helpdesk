from __future__ import annotations

from typing import Protocol

PROMPT_V1 = """You summarize one masked internal IT support ticket.
Return two sections labeled Summary: and Suggested steps:.
Copy placeholders exactly. Do not invent identifiers or facts."""
PROMPT_V2 = """You summarize one masked internal IT support ticket.
Return exactly two sections in this order:
Summary: one or two sentences with the affected system, symptom, and relevant recent change.
Suggested steps: two or three numbered steps supported by the ticket.
Copy every opaque placeholder exactly. Do not modify or invent placeholders, identifiers,
diagnoses, completed actions, or facts. State not provided when required context is absent."""


class Provider(Protocol):
    def summarize(self, masked_ticket: str, prompt_version: str) -> str: ...


class ProviderTimeout(Exception):
    pass


class ProviderFailure(Exception):
    pass


class MockProvider:
    def summarize(self, masked_ticket: str, prompt_version: str) -> str:
        if prompt_version == "v1":
            return f"Summary: {masked_ticket}\nSuggested steps:\n1. Confirm the reported symptoms.\n2. Check relevant device settings."
        context = " Diagnostic context: not provided." if "display is blank" in masked_ticket.lower() else ""
        return (
            f"Summary: {masked_ticket}{context}\nSuggested steps:\n"
            "1. Confirm the reported symptom and any recent change.\n"
            "2. Check the affected system settings using only the supplied ticket facts."
        )
