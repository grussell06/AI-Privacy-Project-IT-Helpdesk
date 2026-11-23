from __future__ import annotations

import unittest
import io
from unittest.mock import patch

from privacy_gateway.cli import handle_request, main
from privacy_gateway.gateway import PrivacyGateway


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = PrivacyGateway.default()

    def test_valid_minimal_request(self) -> None:
        result = handle_request({"request_id": "r1", "text": "Maya Chen needs help."}, self.gateway)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["request_id"], "r1")

    def test_valid_policy_and_prompt(self) -> None:
        result = handle_request({"request_id": "r2", "text": "Email maya.chen@example.test.",
                                 "policies": {"EMAIL": "REMOVE"}, "prompt_version": "v1"}, self.gateway)
        self.assertNotIn("maya.chen@example.test", result["output"])

    def test_invalid_boundaries_return_controlled_errors(self) -> None:
        invalid = [[], {}, {"request_id": "r1"}, {"text": "x"},
                   {"request_id": 1, "text": "x"}, {"request_id": "r1", "text": 2},
                   {"request_id": "r1", "text": "x", "policies": []},
                   {"request_id": "r1", "text": "x", "prompt_version": 2},
                   {"request_id": "r1", "text": "x", "prompt_version": "v9"}]
        for request in invalid:
            with self.subTest(request=request):
                result = handle_request(request, self.gateway)
                self.assertEqual(result["status"], "error")
                self.assertIn("code", result)

    def test_unknown_top_level_field_is_ignored(self) -> None:
        result = handle_request({"request_id": "r3", "text": "Display is blank.", "extra": True}, self.gateway)
        self.assertEqual(result["status"], "ok")

    def test_invalid_json_returns_controlled_error(self) -> None:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO("{")), patch("sys.stdout", output):
            self.assertEqual(main(), 1)
        self.assertIn('"code": "INVALID_JSON"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
