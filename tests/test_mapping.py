from __future__ import annotations

import unittest

from privacy_gateway.mapping import Masker, RequestMapping
from privacy_gateway.models import GatewayError, Match, Policy, PolicyDecision


class MappingTests(unittest.TestCase):
    def test_repeated_masked_value_reuses_token(self) -> None:
        text = "Maya Maya"
        decisions = [
            PolicyDecision(Match(0, 4, "NAME", "Maya"), Policy.MASK),
            PolicyDecision(Match(5, 9, "NAME", "Maya"), Policy.MASK),
        ]
        mapping = RequestMapping("r1")
        masked = Masker().apply(text, decisions, mapping)
        first, second = masked.split()
        self.assertEqual(first, second)
        self.assertNotIn("r1", masked)
        self.assertEqual(len(mapping), 1)

    def test_different_values_get_different_tokens(self) -> None:
        mapping = RequestMapping("r1")
        self.assertNotEqual(mapping.token_for("NAME", "Maya"), mapping.token_for("NAME", "Jordan"))

    def test_remove_normalizes_spaces_and_punctuation(self) -> None:
        decision = PolicyDecision(Match(6, 10, "NAME", "Maya"), Policy.REMOVE)
        mapping = RequestMapping("r1")
        self.assertEqual(Masker().apply("Hello Maya, ticket", [decision], mapping), "Hello, ticket")
        self.assertEqual(len(mapping), 0)

    def test_adjacent_removed_values_do_not_join_words(self) -> None:
        decisions = [PolicyDecision(Match(4, 8, "NAME", "Maya"), Policy.REMOVE),
                     PolicyDecision(Match(9, 15, "NAME", "Jordan"), Policy.REMOVE)]
        self.assertEqual(Masker().apply("Ask Maya Jordan today", decisions, RequestMapping("r1")), "Ask today")

    def test_close_clears_values(self) -> None:
        mapping = RequestMapping("r1")
        mapping.token_for("NAME", "Maya")
        mapping.close()
        self.assertTrue(mapping.closed)
        self.assertEqual(len(mapping), 0)

    def test_closed_mapping_rejects_access(self) -> None:
        mapping = RequestMapping("r1")
        mapping.close()
        with self.assertRaises(GatewayError):
            mapping.token_for("NAME", "Maya")


if __name__ == "__main__":
    unittest.main()
