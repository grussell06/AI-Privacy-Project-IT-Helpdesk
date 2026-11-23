# User Guide

## M3 privacy gateway

The M3 program reads one JSON request from standard input and prints one JSON response.

### Request

```json
{
  "request_id": "r1",
  "text": "Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042. maya.chen@example.test",
  "policies": {"NAME": "MASK", "EMAIL": "REMOVE"},
  "prompt_version": "v2"
}
```

### Run

From the repository root in PowerShell:

```powershell
@'
{"request_id":"r1","text":"Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042. maya.chen@example.test","policies":{"NAME":"MASK","EMAIL":"REMOVE"},"prompt_version":"v2"}
'@ | python src/main.py
```

### Successful response

```json
{
  "status": "ok",
  "request_id": "r1",
  "output": "Summary: Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042.\nSuggested steps:\n1. Confirm the reported symptom and any recent change.\n2. Check the affected system settings using only the supplied ticket facts."
}
```

### Supported synthetic formats

- Names listed in `src/data/synthetic_names.txt`
- Email addresses such as `maya.chen@example.test`
- Asset IDs in the form `LT-48291`
- Ticket numbers in the form `INC-1042`

Input containing `[[...]]` is rejected because that syntax is reserved for gateway placeholders. Invalid provider placeholders produce a controlled `INVALID_PLACEHOLDER` response.

### Run automated tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Missing category policies default to `MASK`. Valid values are `MASK` and `REMOVE`; invalid values return `INVALID_POLICY`. Prompt versions are `v1` and `v2`, with `v2` the default.

Controlled errors include `INVALID_JSON`, `INVALID_REQUEST`, `INVALID_POLICY`, `INVALID_PROMPT`, `RESERVED_SYNTAX`, `INVALID_PLACEHOLDER`, `MALFORMED_RESPONSE`, `PROVIDER_TIMEOUT`, and `PROVIDER_ERROR`. The gateway never retries with unmasked text.

### Run the evaluation

```powershell
$env:PYTHONPATH='src'
python scripts/run_evaluation.py
```

## Retained M1 tech spike

The repository retains the earlier M1 runtime check for milestone history. It reads one line and prints that line back; the current M3 executable is `src/main.py`.

### Requirements

- Python 3.12 or a compatible Python 3 installation
- A terminal opened at the repository root

### Run

```powershell
python src/tech_spike.py
```

The exact Codex runtime command used for the recorded M1 run is available in `docs/DESIGN.md`. On another computer, `python src/tech_spike.py` works after Python is installed and available on the system path.

At the `Input:` prompt, enter one line of synthetic text and press Enter.

Example:

```text
Input: Ticket INC-1042 reports a Wi-Fi problem.
Echo: Ticket INC-1042 reports a Wi-Fi problem.
```

### Current limitations

The retained M1 program only echoes input. Use `src/main.py` for the M3 privacy gateway.

### Data warning

Use synthetic examples only. Do not enter actual employee names, support records, credentials, private contact details, or API keys.

### Troubleshooting

- If `python` is not recognized, install Python 3 or use the command your system provides for Python 3, such as `py`.
- If the program exits after one line, that is expected; the M1 spike handles a single input.
