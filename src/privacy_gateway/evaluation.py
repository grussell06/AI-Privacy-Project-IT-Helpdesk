from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .detection import Detector, OverlapResolver
from .models import Match
from .provider import Provider


@dataclass(frozen=True)
class DetectionCase:
    case_id: str
    text: str
    expected: tuple[Match, ...]


@dataclass(frozen=True)
class DetectionMetrics:
    tp: int
    fp: int
    fn: int
    precision: float | None
    recall: float | None


@dataclass(frozen=True)
class PromptCase:
    case_id: str
    masked_text: str
    required: tuple[str, ...]
    forbidden: tuple[str, ...]


@dataclass(frozen=True)
class PromptScore:
    required_information: int
    output_format: int
    placeholder_handling: int
    no_invented_information: int
    task_usefulness: int

    @property
    def total(self) -> int:
        return sum((self.required_information, self.output_format, self.placeholder_handling,
                    self.no_invented_information, self.task_usefulness))


@dataclass(frozen=True)
class PromptEvaluation:
    case_id: str
    prompt_version: str
    output: str
    score: PromptScore


def _nth_span(text: str, value: str, occurrence: int) -> tuple[int, int]:
    starts = [match.start() for match in re.finditer(re.escape(value), text)]
    start = starts[occurrence - 1]
    return start, start + len(value)


def load_detection_cases(path: Path) -> list[DetectionCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for item in raw:
        expected = []
        for category, value, occurrence in item["expected"]:
            start, end = _nth_span(item["text"], value, occurrence)
            expected.append(Match(start, end, category, value))
        cases.append(DetectionCase(item["id"], item["text"], tuple(expected)))
    return cases


def evaluate_detection(cases: list[DetectionCase], detector: Detector, resolver: OverlapResolver) -> DetectionMetrics:
    tp = fp = fn = 0
    for case in cases:
        actual = {(m.start, m.end, m.category, m.value) for m in resolver.resolve(detector.detect(case.text))}
        expected = {(m.start, m.end, m.category, m.value) for m in case.expected}
        tp += len(actual & expected)
        fp += len(actual - expected)
        fn += len(expected - actual)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return DetectionMetrics(tp, fp, fn, precision, recall)


def count_outbound_leaks(original_values: list[str], outbound: str) -> int:
    return sum(outbound.count(value) for value in set(original_values) if value)


def load_prompt_cases(path: Path) -> list[PromptCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [PromptCase(item["id"], item["masked_text"], tuple(item["required"]), tuple(item["forbidden"])) for item in raw]


def evaluate_prompts(cases: list[PromptCase], provider: Provider) -> list[PromptEvaluation]:
    results = []
    token_pattern = re.compile(r"\[\[.*?\]\]")
    for version in ("v1", "v2"):
        for case in cases:
            output = provider.summarize(case.masked_text, version)
            required = int(all(value.lower() in output.lower() for value in case.required))
            formatted = int(output.startswith("Summary:") and "\nSuggested steps:\n" in output)
            expected_tokens = token_pattern.findall(case.masked_text)
            actual_tokens = token_pattern.findall(output)
            placeholders = int(expected_tokens == actual_tokens)
            no_invention = int(not any(value.lower() in output.lower() for value in case.forbidden))
            identifier_pattern = re.compile(r"\b(?:INC-[0-9]{4}|LT-[0-9]{5}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
            new_identifiers = set(identifier_pattern.findall(output)) - set(identifier_pattern.findall(case.masked_text))
            no_invention = int(bool(no_invention and not new_identifiers))
            useful = int(bool(required and formatted and "1." in output and "do nothing" not in output.lower()))
            score = PromptScore(required, formatted, placeholders, no_invention, useful)
            results.append(PromptEvaluation(case.case_id, version, output, score))
    return results
