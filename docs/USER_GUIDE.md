# User Guide

## M2 privacy gateway

The M2 program reads one JSON request from standard input and prints one JSON response.

### Request

```json
{
  "request_id": "r1",
  "text": "Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042."
}
```

### Run

From the repository root in PowerShell:

```powershell
@'
{"request_id":"r1","text":"Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042."}
'@ | python src/main.py
```

### Successful response

```json
{
  "status": "ok",
  "request_id": "r1",
  "output": "Summary: Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042.\nSuggested steps:\n1. Confirm the reported symptoms and recent changes.\n2. Check the affected device and relevant connection or account settings."
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

The command-line JSON fields remain subject to confirmation against the separate course I/O Contract.

## Retained M1 tech spike

The repository retains the earlier M1 runtime check for milestone history. It reads one line and prints that line back; the M2 executable is `src/main.py`.

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

The retained M1 program only echoes input. Use `src/main.py` for the M2 privacy gateway.

### Data warning

Use synthetic examples only. Do not enter actual employee names, support records, credentials, private contact details, or API keys.

### Troubleshooting

- If `python` is not recognized, install Python 3 or use the command your system provides for Python 3, such as `py`.
- If the program exits after one line, that is expected; the M1 spike handles a single input.
