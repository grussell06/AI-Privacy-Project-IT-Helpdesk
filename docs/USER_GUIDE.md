# User Guide

## M1 tech spike

The current executable is a small runtime check. It reads one line and prints that line back. It is not yet a privacy gateway and does not mask sensitive values.

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

The M1 program only echoes input. It does not detect sensitive data, mask identifiers, contact a provider, validate responses, or restore values. Those features begin in M2.

### Data warning

Use synthetic examples only. Do not enter actual employee names, support records, credentials, private contact details, or API keys.

### Troubleshooting

- If `python` is not recognized, install Python 3 or use the command your system provides for Python 3, such as `py`.
- If the program exits after one line, that is expected; the M1 spike handles a single input.
