# Design

## Problem and intended user

The intended user is an internal IT support technician. The technician receives help-desk tickets that mix a technical problem with employee identifiers. The narrow AI-assisted task is to transform one ticket into a concise problem summary and a short list of suggested troubleshooting steps.

The motivation is to preserve the useful technical context while preventing unnecessary disclosure of identifiers to an external AI provider. A summary such as "Windows laptop cannot connect to the office Wi-Fi after a password reset" remains useful without exposing the employee's name, email address, device asset ID, or ticket number.

## Sensitive-data categories

The planned final system supports four categories:

| Category | Synthetic example | Planned detection method |
---
| Employee name | Maya Chen | Exact match from a local synthetic term list |
| Email address | maya.chen@example.test | Documented structured pattern |
| Device asset ID | LT-48291 | Documented structured pattern such as `LT-[0-9]{5}` |
| Ticket number | INC-1042 | Documented structured pattern such as `INC-[0-9]{4}` |

Names will come from a local, synthetic allowlist because universal name recognition is outside the project scope. Structured patterns will be intentionally narrow and documented to keep behavior explainable.

## Useful output and success criteria

A successful final output:

1. states the central technical problem accurately;
2. includes short, relevant troubleshooting steps;
3. invents no facts, actions, or identifiers;
4. contains only identifiers authorized for restoration;
5. never sends an original protected value in the outbound provider payload;
6. returns a controlled error instead of unsafe output when placeholder validation fails.

For the M1 design, these criteria are represented by specific planned acceptance cases in `docs/EVALUATION.md`. M2 will automate the applicable cases.

## Non-goals

- Processing real employee or customer data
- Detecting every possible personal identifier
- Reading attachments, screenshots, or scanned documents
- Multi-turn conversations or persistent request history
- A graphical interface or complete ticketing application
- A live or paid AI integration
- Giving the provider permission to restore or invent protected values

## M2 scope

M2 will implement one command-line, single-turn pipeline using synthetic tickets and an offline deterministic mock provider. It will include:

- local exact matching for synthetic employee names;
- structured matching for email addresses, asset IDs, and ticket numbers;
- local masking and one request-local placeholder map;
- a mock provider that produces a predictable summary;
- response placeholder validation and local restoration;
- automated versions of the relevant M1 acceptance cases;
- controlled failure for invalid reserved placeholders.

Full category policy, cross-request isolation, overlap hardening, simulated provider failures, and prompt comparison remain later-milestone work unless a small supporting piece is needed earlier.

## Data flow and trust boundary

```text
LOCAL MACHINE                                         EXTERNAL/PROVIDER SIDE

Synthetic ticket
      |
      v
Detector -> policy -> masker -> masked request ---------> provider/mock
                         |                                    |
                         | request-local mapping              |
                         | stays local                        v
                         +<-- validator <- masked response ---+
                                  |
                                  v
                           local restoration
                                  |
                                  v
                         final summary or error
```

Only the masked ticket and versioned task prompt may cross the boundary. Detection rules, original values, placeholder mappings, policy decisions, validation results, and restored output stay local. The response must be validated before restoration.

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| Input layer | Read one synthetic ticket for one request |
| Detector | Find explainable exact-list and structured-pattern matches |
| Policy | Decide whether each detected category is masked or removed |
| Masker | Replace selected spans and create the request-local mapping |
| Provider interface | Send only masked content; M2 uses an offline mock |
| Validator | Reject malformed, unknown, modified, or unauthorized placeholders |
| Restorer | Restore only placeholders valid for the current request |
| Output layer | Return a useful summary or a controlled error |

These responsibilities are separated so detection, external communication, and restoration can be tested independently. The mapping belongs to one request and should be released after that request completes.

## Placeholder design

The initial form is:

```text
[[request_id:CATEGORY:index]]
```

Example placeholders:

```text
[[r7:NAME:1]]
[[r7:EMAIL:1]]
[[r7:ASSET:1]]
[[r7:TICKET:1]]
```

The request ID supports later checks against placeholders from another request. The category keeps validation explainable, and the index distinguishes different entities of the same category. Repeated occurrences of the same original value within one request should use the same placeholder. Input containing reserved placeholder syntax will be rejected rather than treated as ordinary text.

## Initial provider prompt

Prompt version: `it-summary-v1`

```text
You summarize one masked internal IT support ticket.

Return exactly two sections:
Summary: one or two sentences describing the reported technical problem.
Suggested steps: two or three short troubleshooting steps supported by the ticket.

Text enclosed in double square brackets is an opaque placeholder. Copy every
placeholder exactly when it is relevant. Do not modify, remove, expand, interpret,
or invent placeholders. Do not invent facts, diagnoses, completed actions, or
identifiers. If the ticket lacks enough information, say what information is missing.

Ticket:
{masked_ticket}
```

The prompt asks the provider to preserve opaque tokens, but prompt compliance is not considered a security boundary. Local response validation remains mandatory.

## Language and runtime choice

The selected implementation language is Python 3.12. The realistic alternative is TypeScript running on Node.js.

| Trade-off | Python | TypeScript |
| --- | --- | --- |
| String processing | Standard-library regular expressions and direct string manipulation support a small text pipeline with little setup. | Regular expressions are also capable, but project setup and build configuration add work for a command-line prototype. |
| Types and contracts | Type hints and data classes document structures, but ordinary execution does not enforce hints. Explicit runtime validation is still needed. | Discriminated unions and strict static checking can make request, policy, and result states harder to mix accidentally. Runtime JSON still requires validation. |
| Testing and iteration | The standard library supports a compact offline test suite, which fits the semester scope and quick synthetic experiments. | Mature test frameworks are available, but they add package and configuration choices that do not directly improve the small M1/M2 pipeline. |
| JSON and deployment | JSON is built in, and the program can run directly where Python is installed. | JSON is native to the platform, and compiled JavaScript is easy to run where Node.js is installed. |

Python is selected because the project is a small command-line text-processing system and rapid, readable iteration matters most. TypeScript's stronger static contracts are a meaningful advantage, so the Python design will compensate with explicit data structures, runtime validation at trust boundaries, and automated tests.

## Tech spike

The M1 spike confirms that the selected runtime can read and echo text.

- Runtime: Python 3.12.14
- File: `src/tech_spike.py`
- Exact command: `python src/tech_spike.py`
- Synthetic input: `Ticket INC-1042 reports a Wi-Fi problem.`
- Observed output: `Echo: Ticket INC-1042 reports a Wi-Fi problem.`

The spike does not detect, mask, send, validate, or restore information.

## Initial design decisions

1. Use a local synthetic name list instead of general named-entity recognition so matches are explainable and reproducible.
2. Use request-scoped placeholders containing a request ID to support later authorization checks.
3. Treat the prompt as task guidance and local validation as the enforcement mechanism.
4. Use an offline deterministic mock provider for reproducible gateway tests.
