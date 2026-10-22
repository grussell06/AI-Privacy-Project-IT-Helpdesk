# AI Privacy Gateway for IT Support Tickets

## Project overview

This project explores whether an IT support technician can use an AI system to summarize help-desk tickets while keeping sensitive identifiers local.

The gateway detects selected sensitive values, replaces them with placeholders, sends only masked text to a deterministic offline mock provider, validates the response, and restores authorized values locally.

## Intended user and task

The intended user is an internal IT support technician.

The system transforms one synthetic IT support ticket into:

- A concise description of the technical problem
- A short list of suggested troubleshooting steps

## Sensitive-data categories

The M2 prototype protects:

- Employee names from a local synthetic term list
- Email addresses
- Device asset IDs
- Ticket numbers

Only synthetic data is used.

## Current milestone

This repository currently contains the M2 working prototype.

M2 includes:

- A complete input-to-output privacy pipeline
- Exact name matching from a local synthetic term list
- Structured patterns for emails, asset IDs, and ticket numbers
- Local masking and request-local placeholder mappings
- A deterministic offline mock provider
- Provider-response validation
- Local restoration of authorized placeholders
- Preservation of repeated values
- Different placeholders for different entities
- Controlled errors for invalid reserved placeholders
- Eight automated tests
- Updated design, evaluation, user guide, and assistance records

A real AI API, graphical interface, multi-turn conversation, MASK/REMOVE policy, and prompt comparison are not required for M2.

## Repository structure

```text
.
├── README.md
├── docs/
│   ├── ASSISTANCE.md
│   ├── DESIGN.md
│   ├── EVALUATION.md
│   └── USER_GUIDE.md
├── src/
│   ├── data/
│   │   └── synthetic_names.txt
│   ├── privacy_gateway/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   └── gateway.py
│   ├── main.py
│   └── tech_spike.py
└── tests/
    └── test_gateway.py
```

## Requirements

- Python 3.12 or another compatible Python 3 version

Check your installed version with:

```powershell
python --version
```

## Run the privacy gateway

From the repository's root directory in PowerShell, run:

```powershell
@'
{"request_id":"r1","text":"Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042."}
'@ | python src/main.py
```

Expected output:

```json
{
  "status": "ok",
  "request_id": "r1",
  "output": "Summary: Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042.\nSuggested steps:\n1. Confirm the reported symptoms and recent changes.\n2. Check the affected device and relevant connection or account settings."
}
```

The original protected values are masked before the offline provider receives the ticket. They are restored only after the provider response passes local validation.

## Run the automated tests

From the repository's root directory in PowerShell, run:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 8 tests
OK
```

## Documentation

- `docs/DESIGN.md` contains the requirements, architecture, language reasoning, implemented components, placeholder design, prompt, and execution trace.
- `docs/EVALUATION.md` contains the synthetic acceptance cases, automated-test evidence, and observed results.
- `docs/USER_GUIDE.md` contains detailed setup, usage, supported formats, errors, and troubleshooting information.
- `docs/ASSISTANCE.md` records important assistance, project decisions, and verification.

## Data and privacy notice

Do not use real support tickets, employee information, credentials, API keys, or private records. All project inputs, term-list entries, and examples must be synthetic.

