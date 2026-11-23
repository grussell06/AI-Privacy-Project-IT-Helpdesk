from __future__ import annotations

import json
import sys

from .gateway import GatewayError, PrivacyGateway


def error(code: str, message: str) -> dict[str, object]:
    return {"status": "error", "code": code, "message": message}


def handle_request(request: object, gateway: PrivacyGateway) -> dict[str, object]:
    if not isinstance(request, dict):
        return error("INVALID_REQUEST", "input must be a JSON object")
    request_id = request.get("request_id")
    text = request.get("text")
    policies = request.get("policies")
    prompt_version = request.get("prompt_version")
    if not isinstance(request_id, str) or not isinstance(text, str):
        return error("INVALID_REQUEST", "request_id and text must be strings")
    if policies is not None and not isinstance(policies, dict):
        return error("INVALID_POLICY", "policies must be an object")
    if prompt_version is not None and not isinstance(prompt_version, str):
        return error("INVALID_PROMPT", "prompt_version must be a string")
    try:
        result = gateway.process(request_id, text, policies, prompt_version)
        return {"status": "ok", "request_id": result.request_id, "output": result.output}
    except GatewayError as exc:
        return error(exc.code, exc.message)


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        response = error("INVALID_JSON", "input is not valid JSON")
    else:
        response = handle_request(request, PrivacyGateway.default())
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
