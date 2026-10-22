"""Provisional JSON-lines command-line interface for the M2 gateway."""

from __future__ import annotations

import json
import sys

from .gateway import GatewayError, PrivacyGateway


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict):
            raise GatewayError("INVALID_REQUEST", "Input must be a JSON object")

        gateway = PrivacyGateway.default()
        result = gateway.process(request.get("request_id", ""), request.get("text"))
        response = {
            "status": "ok",
            "request_id": result.request_id,
            "output": result.output,
        }
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return 0
    except json.JSONDecodeError:
        error = {"status": "error", "code": "INVALID_JSON", "message": "Input is not valid JSON"}
    except GatewayError as exc:
        error = {"status": "error", "code": exc.code, "message": exc.message}

    print(json.dumps(error, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
