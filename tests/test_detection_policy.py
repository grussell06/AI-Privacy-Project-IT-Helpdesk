from __future__ import annotations

import unittest

from privacy_gateway.detection import Detector, OverlapResolver
from privacy_gateway.models import GatewayError, Match, Policy
from privacy_gateway.policy import PolicyEngine


class DetectionPolicyTests(unittest.TestCase):
    def test_detects_four_supported_categories(self) -> None:
        detector = Detector(["Maya Chen"])
        found = detector.detect(
            "Maya Chen maya.chen@example.test LT-48291 INC-1042"
        )
        self.assertEqual({m.category for m in found}, {"NAME", "EMAIL", "ASSET", "TICKET"})

    def test_longest_name_wins_overlap(self) -> None:
        found = Detector(["Lane", "Evan Lane"]).detect("Evan Lane called.")
        resolved = OverlapResolver().resolve(found)
        self.assertEqual([(m.category, m.value) for m in resolved], [("NAME", "Evan Lane")])

    def test_category_priority_breaks_equal_length_tie(self) -> None:
        candidates = [Match(0, 5, "NAME", "abcde"), Match(0, 5, "EMAIL", "abcde")]
        self.assertEqual(OverlapResolver().resolve(candidates)[0].category, "EMAIL")

    def test_overlap_output_is_sorted_by_source_position(self) -> None:
        candidates = [Match(10, 15, "NAME", "later"), Match(0, 5, "NAME", "early")]
        self.assertEqual([m.start for m in OverlapResolver().resolve(candidates)], [0, 10])

    def test_punctuation_does_not_prevent_structured_matches(self) -> None:
        found = Detector([]).detect("(LT-48291), INC-1042; a@example.test.")
        self.assertEqual({m.category for m in found}, {"EMAIL", "ASSET", "TICKET"})

    def test_missing_policy_defaults_to_mask(self) -> None:
        decision = PolicyEngine().resolve([Match(0, 4, "NAME", "Maya")], None)[0]
        self.assertEqual(decision.policy, Policy.MASK)

    def test_explicit_remove_and_mixed_policies(self) -> None:
        matches = [Match(0, 4, "NAME", "Maya"), Match(5, 10, "EMAIL", "a@b.c")]
        decisions = PolicyEngine().resolve(matches, {"EMAIL": "REMOVE"})
        self.assertEqual([d.policy for d in decisions], [Policy.MASK, Policy.REMOVE])

    def test_invalid_policy_value_is_controlled_error(self) -> None:
        with self.assertRaises(GatewayError) as caught:
            PolicyEngine().resolve([], {"NAME": "HIDE"})
        self.assertEqual(caught.exception.code, "INVALID_POLICY")

    def test_unknown_policy_category_is_controlled_error(self) -> None:
        with self.assertRaises(GatewayError) as caught:
            PolicyEngine().resolve([], {"PHONE": "MASK"})
        self.assertEqual(caught.exception.code, "INVALID_POLICY")


if __name__ == "__main__":
    unittest.main()
