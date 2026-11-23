from __future__ import annotations

import unittest

from privacy_gateway.gateway import GatewayError, PrivacyGateway
from privacy_gateway.mapping import RequestMapping
from privacy_gateway.provider import ProviderFailure, ProviderTimeout


VALID_STEPS = "\nSuggested steps:\n1. Check the device."


class FixedProvider:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def summarize(self, masked_ticket: str, prompt_version: str) -> str:
        self.calls.append((masked_ticket, prompt_version))
        return self.response  # type: ignore[return-value]


class RaisingProvider(FixedProvider):
    def __init__(self, error: Exception) -> None:
        super().__init__("")
        self.error = error

    def summarize(self, masked_ticket: str, prompt_version: str) -> str:
        self.calls.append((masked_ticket, prompt_version))
        raise self.error


class CapturingFactory:
    def __init__(self) -> None:
        self.created: list[RequestMapping] = []

    def __call__(self, request_id: str) -> RequestMapping:
        mapping = RequestMapping(request_id)
        self.created.append(mapping)
        return mapping


class PrivacyGatewayTests(unittest.TestCase):
    def test_request_id_never_appears_in_outbound_placeholder(self) -> None:
        result = PrivacyGateway.default().process("INC-1042", "Ticket INC-1042 needs review.")
        self.assertNotIn("INC-1042", result.masked_text)

    def test_reused_public_request_id_gets_unique_placeholder_namespace(self) -> None:
        first = PrivacyGateway.default().process("same", "Maya Chen cannot sign in.")
        second = PrivacyGateway.default().process("same", "Jordan Lee reports no audio.")
        self.assertNotEqual(first.masked_text.split()[0], second.masked_text.split()[0])

    def test_invalid_prompt_types_do_not_call_provider(self) -> None:
        for value in ("", False, 0, [], {}):
            provider = FixedProvider("Summary: x" + VALID_STEPS)
            with self.subTest(value=value), self.assertRaises(GatewayError) as caught:
                PrivacyGateway(PrivacyGateway.default().detector, provider).process("r0", "text", prompt_version=value)  # type: ignore[arg-type]
            self.assertEqual(caught.exception.code, "INVALID_PROMPT")
            self.assertEqual(provider.calls, [])

    def test_ordinary_input_masks_and_restores_supported_values(self) -> None:
        result = PrivacyGateway.default().process(
            "r1", "Maya Chen uses maya.chen@example.test on LT-48291 for INC-1042."
        )
        for value in ("Maya Chen", "maya.chen@example.test", "LT-48291", "INC-1042"):
            self.assertNotIn(value, result.masked_text)
            self.assertIn(value, result.output)

    def test_remove_value_is_not_restored(self) -> None:
        result = PrivacyGateway.default().process(
            "r2", "Email maya.chen@example.test about INC-1042.", {"EMAIL": "REMOVE"}
        )
        self.assertNotIn("maya.chen@example.test", result.masked_text)
        self.assertNotIn("maya.chen@example.test", result.output)

    def test_independent_requests_reject_foreign_placeholder(self) -> None:
        provider = FixedProvider("Summary: [[r1:NAME:1]] reports audio trouble." + VALID_STEPS)
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process(
                "r2", "Jordan Lee reports audio trouble."
            )
        self.assertEqual(caught.exception.code, "INVALID_PLACEHOLDER")

    def test_unknown_placeholder_is_rejected(self) -> None:
        provider = FixedProvider("Summary: [[r3:NAME:99]] reports trouble." + VALID_STEPS)
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process("r3", "Jordan Lee reports trouble.")
        self.assertEqual(caught.exception.code, "INVALID_PLACEHOLDER")

    def test_malformed_placeholder_is_rejected(self) -> None:
        provider = FixedProvider("Summary: [[r3:NAME:1] reports trouble." + VALID_STEPS)
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process("r3", "Jordan Lee reports trouble.")
        self.assertEqual(caught.exception.code, "INVALID_PLACEHOLDER")

    def test_modified_placeholder_is_rejected(self) -> None:
        provider = FixedProvider("Summary: [[r3:NAME:1x]] reports trouble." + VALID_STEPS)
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process("r3", "Jordan Lee reports trouble.")
        self.assertEqual(caught.exception.code, "INVALID_PLACEHOLDER")

    def test_malformed_response_variants(self) -> None:
        invalid = [None, "", "Summary: text", "Suggested steps:\n1. X\nSummary: text", "summary: text" + VALID_STEPS,
                   "Summary: \nSuggested steps:\n1. X", "Summary: text\nSuggested steps:\nnone",
                   "Summary: text\nSuggested steps:\n1.\n\nOnly prose",
                   "Summary: text\nSuggested steps:\n1. X\nSummary: duplicate"]
        for response in invalid:
            with self.subTest(response=response), self.assertRaises(GatewayError) as caught:
                PrivacyGateway(PrivacyGateway.default().detector, FixedProvider(response)).process("r4", "No sensitive data.")
            self.assertEqual(caught.exception.code, "MALFORMED_RESPONSE")

    def test_provider_timeout_is_controlled_and_not_retried(self) -> None:
        provider = RaisingProvider(ProviderTimeout())
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process("r5", "Maya Chen needs help.")
        self.assertEqual(caught.exception.code, "PROVIDER_TIMEOUT")
        self.assertEqual(len(provider.calls), 1)
        self.assertNotIn("Maya Chen", provider.calls[0][0])

    def test_provider_error_is_controlled_and_not_retried(self) -> None:
        provider = RaisingProvider(ProviderFailure())
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway(PrivacyGateway.default().detector, provider).process("r6", "Maya Chen needs help.")
        self.assertEqual(caught.exception.code, "PROVIDER_ERROR")
        self.assertEqual(len(provider.calls), 1)

    def test_mapping_is_closed_after_success_and_failure(self) -> None:
        for provider in (FixedProvider("Summary: Safe text." + VALID_STEPS), RaisingProvider(ProviderFailure())):
            factory = CapturingFactory()
            gateway = PrivacyGateway(PrivacyGateway.default().detector, provider, mapping_factory=factory)
            try:
                gateway.process("r7", "Maya Chen needs help.")
            except GatewayError:
                pass
            self.assertEqual(len(factory.created), 1)
            self.assertTrue(factory.created[0].closed)
            self.assertEqual(len(factory.created[0]), 0)

    def test_mapping_is_closed_after_each_failure_class(self) -> None:
        providers = [RaisingProvider(ProviderTimeout()), RaisingProvider(ProviderFailure()),
                     FixedProvider(""), FixedProvider("Summary: [[foreign:NAME:1]] x." + VALID_STEPS)]
        for provider in providers:
            factory = CapturingFactory()
            with self.subTest(provider=type(provider).__name__), self.assertRaises(GatewayError):
                PrivacyGateway(PrivacyGateway.default().detector, provider, mapping_factory=factory).process("r9", "Maya Chen needs help.")
            self.assertTrue(factory.created[0].closed)
            self.assertEqual(len(factory.created[0]), 0)

    def test_reserved_syntax_in_input_is_rejected(self) -> None:
        with self.assertRaises(GatewayError) as caught:
            PrivacyGateway.default().process("r8", "Contains [[r8:NAME:1]].")
        self.assertEqual(caught.exception.code, "RESERVED_SYNTAX")


if __name__ == "__main__":
    unittest.main()
