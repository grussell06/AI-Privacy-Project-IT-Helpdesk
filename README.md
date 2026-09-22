# AI Privacy Gateway for IT Support Tickets

## Project overview

This project explores whether an IT support technician can use an AI system to summarize help-desk tickets while keeping sensitive identifiers local.

The planned gateway will detect selected sensitive values, replace them with placeholders, send only masked text to an offline mock AI provider, validate the response, and restore authorized values locally.

## Intended user and task

The intended user is an internal IT support technician.

The system will transform one synthetic IT support ticket into:

- A concise description of the technical problem
- A short list of suggested troubleshooting steps

## Sensitive-data categories

The project plans to protect:

- Employee names
- Email addresses
- Device asset IDs
- Ticket numbers

Only synthetic data will be used.

## Current milestone

This repository currently contains the M1 requirements and design work.

M1 includes:

- Project requirements and scope
- Planned acceptance cases
- Python and TypeScript comparison
- System architecture and privacy boundary
- Placeholder design
- Initial provider prompt
- Read-and-echo tech spike
- Assistance record

A working privacy gateway is not required until M2.

## Repository structure

```text
.
├── README.md
├── docs/
│   ├── ASSISTANCE.md
│   ├── DESIGN.md
│   ├── EVALUATION.md
│   └── USER_GUIDE.md
└── src/
    └── tech_spike.py
```

## Requirements

- Python 3.12 or another compatible Python 3 version

Check your installed version with:

```powershell
python --version
```

## Run the tech spike

From the repository’s root directory, run:

```powershell
python src/tech_spike.py
```

Example interaction:

```text
Input: Ticket INC-1042 reports a Wi-Fi problem.
Echo: Ticket INC-1042 reports a Wi-Fi problem.
```

The M1 tech spike only verifies that Python can read and echo text. It does not perform detection, masking, validation, or restoration.

## Documentation

- `docs/DESIGN.md` contains the requirements, architecture, language comparison, placeholder design, initial prompt, and M2 scope.
- `docs/EVALUATION.md` contains the planned synthetic acceptance cases.
- `docs/USER_GUIDE.md` contains detailed setup and usage instructions.
- `docs/ASSISTANCE.md` records important assistance, project decisions, and verification.

## Data and privacy notice

Do not use real support tickets, employee information, credentials, API keys, or private records. All project inputs and examples must be synthetic.