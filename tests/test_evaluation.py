from __future__ import annotations

import unittest
from pathlib import Path

from privacy_gateway.detection import Detector, OverlapResolver
from privacy_gateway.evaluation import (
    count_outbound_leaks, evaluate_detection, evaluate_prompts,
    load_detection_cases, load_prompt_cases,
)
from privacy_gateway.provider import MockProvider
from privacy_gateway.provider import PROMPT_V1, PROMPT_V2


FIXTURES = Path(__file__).parent / "fixtures"


class EvaluationTests(unittest.TestCase):
    def test_prompt_texts_document_their_contracts(self) -> None:
        self.assertIn("Summary:", PROMPT_V1)
        self.assertIn("Suggested steps:", PROMPT_V1)
        self.assertIn("numbered", PROMPT_V2)
        self.assertIn("not provided", PROMPT_V2)
    def test_detection_metrics_have_expected_counts(self) -> None:
        cases = load_detection_cases(FIXTURES / "detection_cases.json")
        metrics = evaluate_detection(cases, Detector(["Maya Chen", "Jordan Lee", "Priya Shah", "Evan Lane", "Lane"]), OverlapResolver())
        self.assertEqual((metrics.tp, metrics.fp, metrics.fn), (10, 1, 1))
        self.assertAlmostEqual(metrics.precision or 0, 10 / 11)
        self.assertAlmostEqual(metrics.recall or 0, 10 / 11)

    def test_zero_denominators_are_none(self) -> None:
        metrics = evaluate_detection([], Detector([]), OverlapResolver())
        self.assertIsNone(metrics.precision)
        self.assertIsNone(metrics.recall)

    def test_leaks_count_repeated_occurrences(self) -> None:
        self.assertEqual(count_outbound_leaks(["Maya", "INC-1"], "Maya x Maya INC-1"), 3)
        self.assertEqual(count_outbound_leaks(["Maya"], "[[r1:NAME:1]]"), 0)
        self.assertEqual(count_outbound_leaks(["Maya", "Maya"], "Maya Maya"), 2)

    def test_invented_identifier_and_unhelpful_steps_fail_scoring(self) -> None:
        class BadProvider:
            def summarize(self, masked_ticket: str, prompt_version: str) -> str:
                return f"Summary: {masked_ticket} The motherboard was replaced. New ticket INC-9999.\nSuggested steps:\n1. Do nothing."
        results = evaluate_prompts(load_prompt_cases(FIXTURES / "prompt_cases.json"), BadProvider())
        self.assertTrue(all(item.score.no_invented_information == 0 for item in results))
        self.assertTrue(all(item.score.task_usefulness == 0 for item in results))

    def test_prompt_comparison_is_deterministic_and_v2_scores_higher(self) -> None:
        cases = load_prompt_cases(FIXTURES / "prompt_cases.json")
        first = evaluate_prompts(cases, MockProvider())
        second = evaluate_prompts(cases, MockProvider())
        self.assertEqual(first, second)
        self.assertEqual(len(first), 6)
        totals = {version: sum(item.score.total for item in first if item.prompt_version == version) for version in ("v1", "v2")}
        self.assertGreater(totals["v2"], totals["v1"])
        for item in first:
            self.assertEqual(item.score.placeholder_handling, 1)
            self.assertEqual(item.score.no_invented_information, 1)


if __name__ == "__main__":
    unittest.main()
