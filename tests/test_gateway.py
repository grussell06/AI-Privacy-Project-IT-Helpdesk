"""Automated M2 acceptance tests for the privacy gateway."""

from __future__ import annotations

import unittest

from privacy_gateway.gateway import GatewayError, MockProvider, PrivacyGateway


class FixedProvider(MockProvider):
    def __init__(self, response: str) -> None:
        self.response = response

    def summarize(self, masked_ticket: str) -> str:
        return self.response


class PrivacyGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = PrivacyGateway.default()

    def test_ordinary_input_masks_and_restores_supported_values(self) -> None:
        text = (
            "Maya Chen reports that laptop LT-48291 cannot connect to Wi-Fi. "
            "Contact maya.chen@example.test. Ticket INC-1042."
        )

        result = self.gateway.process("r1", text)

        for protected in (
            "Maya Chen",
            "LT-48291",
            "maya.chen@example.test",
            "INC-1042",
        ):
            self.assertNotIn(protected, result.masked_text)
            self.assertIn(protected, result.output)
        self.assertIn("[[r1:NAME:1]]", result.masked_text)
        self.assertIn("[[r1:EMAIL:1]]", result.masked_text)
        self.assertIn("[[r1:ASSET:1]]", result.masked_text)
        self.assertIn("[[r1:TICKET:1]]", result.masked_text)

    def test_repeated_values_reuse_the_same_placeholder(self) -> None:
        text = (
            "Maya Chen cannot sign in. Maya Chen requested an update at "
            "maya.chen@example.test; reply to maya.chen@example.test. Ticket INC-1043."
        )

        result = self.gateway.process("r2", text)

        self.assertEqual(result.masked_text.count("[[r2:NAME:1]]"), 2)
        self.assertEqual(result.masked_text.count("[[r2:EMAIL:1]]"), 2)
        self.assertNotIn("[[r2:NAME:2]]", result.masked_text)
        self.assertEqual(result.output.count("Maya Chen"), 2)

    def test_different_names_receive_different_placeholders(self) -> None:
        result = self.gateway.process(
            "r3", "Maya Chen transferred ticket INC-1045 to Jordan Lee."
        )

        self.assertIn("[[r3:NAME:1]]", result.masked_text)
        self.assertIn("[[r3:NAME:2]]", result.masked_text)

    def test_no_sensitive_data_passes_through_unchanged(self) -> None:
        text = "The conference-room display is blank after waking from sleep."

        result = self.gateway.process("r4", text)

        self.assertEqual(result.masked_text, text)
        self.assertIn(text, result.output)

    def test_unknown_provider_placeholder_returns_controlled_error(self) -> None:
        gateway = PrivacyGateway(
            self.gateway.detector,
            FixedProvider("Summary: [[r5:NAME:99]] has no audio."),
        )

        with self.assertRaises(GatewayError) as context:
            gateway.process("r5", "Jordan Lee reports no audio on LT-10007.")

        self.assertEqual(context.exception.code, "INVALID_PLACEHOLDER")

    def test_malformed_provider_placeholder_returns_controlled_error(self) -> None:
        gateway = PrivacyGateway(
            self.gateway.detector,
            FixedProvider("Summary: [[r5:NAME:1] has no audio."),
        )

        with self.assertRaises(GatewayError) as context:
            gateway.process("r5", "Jordan Lee reports no audio on LT-10007.")

        self.assertEqual(context.exception.code, "INVALID_PLACEHOLDER")

    def test_foreign_request_placeholder_returns_controlled_error(self) -> None:
        gateway = PrivacyGateway(
            self.gateway.detector,
            FixedProvider("Summary: [[r6:NAME:1]] has no audio."),
        )

        with self.assertRaises(GatewayError) as context:
            gateway.process("r7", "Jordan Lee reports no audio on LT-10007.")

        self.assertEqual(context.exception.code, "INVALID_PLACEHOLDER")

    def test_reserved_placeholder_syntax_in_input_is_rejected(self) -> None:
        with self.assertRaises(GatewayError) as context:
            self.gateway.process("r8", "The ticket contains [[r8:NAME:1]].")

        self.assertEqual(context.exception.code, "RESERVED_SYNTAX")


if __name__ == "__main__":
    unittest.main()
