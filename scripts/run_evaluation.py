from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from privacy_gateway.detection import Detector, OverlapResolver
from privacy_gateway.evaluation import (
    count_outbound_leaks,
    evaluate_detection,
    evaluate_prompts,
    load_detection_cases,
    load_prompt_cases,
)
from privacy_gateway.gateway import PrivacyGateway
from privacy_gateway.provider import MockProvider


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
NAMES = ROOT / "src" / "data" / "synthetic_names.txt"


def main() -> None:
    detector = Detector.from_file(NAMES)
    detection_cases = load_detection_cases(FIXTURES / "detection_cases.json")
    metrics = evaluate_detection(detection_cases, detector, OverlapResolver())
    gateway = PrivacyGateway(detector)
    leaks = 0
    for index, case in enumerate(detection_cases, start=1):
        result = gateway.process(f"e{index}", case.text)
        leaks += count_outbound_leaks([match.value for match in case.expected], result.masked_text)

    prompt_results = evaluate_prompts(load_prompt_cases(FIXTURES / "prompt_cases.json"), MockProvider())
    output = {
        "provider_kind": "offline deterministic mock",
        "detection": {
            "tp": metrics.tp,
            "fp": metrics.fp,
            "fn": metrics.fn,
            "precision": metrics.precision if metrics.precision is not None else "N/A",
            "recall": metrics.recall if metrics.recall is not None else "N/A",
        },
        "outbound_privacy_leaks": leaks,
        "prompt_results": [
            {
                "case_id": item.case_id,
                "prompt_version": item.prompt_version,
                "output": item.output,
                "score": {**asdict(item.score), "total": item.score.total},
            }
            for item in prompt_results
        ],
        "prompt_totals": {
            version: sum(item.score.total for item in prompt_results if item.prompt_version == version)
            for version in ("v1", "v2")
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
