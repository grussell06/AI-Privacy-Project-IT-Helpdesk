# Design

## Problem and intended user

The intended user is an internal IT support technician. The technician receives help-desk tickets that mix a technical problem with employee identifiers. The narrow AI-assisted task is to transform one ticket into a concise problem summary and a short list of suggested troubleshooting steps.

The motivation is to preserve the useful technical context while preventing unnecessary disclosure of identifiers to an external AI provider. A summary such as "Windows laptop cannot connect to the office Wi-Fi after a password reset" remains useful without exposing the employee's name, email address, device asset ID, or ticket number.

## Implemented sensitive-data categories

The M3 system supports four categories:

| Category | Synthetic example | Implemented detection method |
| --- | --- | --- |
| Employee name | Maya Chen | Exact match from a local synthetic term list |
| Email address | maya.chen@example.test | Documented structured pattern |
| Device asset ID | LT-48291 | Documented structured pattern such as `LT-[0-9]{5}` |
| Ticket number | INC-1042 | Documented structured pattern such as `INC-[0-9]{4}` |

Names come from the local synthetic term list at `src/data/synthetic_names.txt` because universal name recognition is outside the project scope. The structured patterns are intentionally narrow and documented to keep behavior explainable.

## Useful output and success criteria

A successful final output:

1. states the central technical problem accurately;
2. includes short, relevant troubleshooting steps;
3. invents no facts, actions, or identifiers;
4. contains only identifiers authorized for restoration;
5. never sends an original protected value in the outbound provider payload;
6. returns a controlled error instead of unsafe output when placeholder validation fails.

The relevant criteria are exercised by the automated M2 acceptance cases in `tests/test_gateway.py` and recorded in `docs/EVALUATION.md`.

## Non-goals

- Processing real employee or customer data
- Detecting every possible personal identifier
- Reading attachments, screenshots, or scanned documents
- Multi-turn conversations or persistent request history
- A graphical interface or complete ticketing application
- A live or paid AI integration
- Giving the provider permission to restore or invent protected values

## M2 scope

M2 implements one command-line, single-turn pipeline using synthetic tickets and an offline deterministic mock provider. It includes:

- local exact matching for synthetic employee names;
- structured matching for email addresses, asset IDs, and ticket numbers;
- local masking and one request-local placeholder map;
- a mock provider that produces a predictable summary;
- response placeholder validation and local restoration;
- automated versions of the relevant M1 acceptance cases;
- controlled failure for invalid reserved placeholders.

At M2, MASK/REMOVE policy, full request-state testing, overlap hardening, simulated provider failures, and prompt comparison were deferred. M3 implements and evaluates these behaviors.

## M2 implementation

The working prototype implements one complete request through these classes:

- `Detector` loads a local synthetic name list and applies documented patterns.
- `Masker` issues request-scoped placeholders and stores the local mapping.
- `MockProvider` returns deterministic offline output.
- `ResponseValidator` rejects malformed, unknown, and foreign-request placeholders.
- `Restorer` replaces only tokens present in the current request mapping.
- `PrivacyGateway` controls the pipeline and keeps the mapping inside one call.
- `cli.py` converts between command-line JSON and controlled result objects.

The repository documents and tests its JSON command-line contract; there is no separate shared course contract.

## M3 reliability architecture

M3 separates `Detector`, `OverlapResolver`, `PolicyEngine`, `RequestMapping`, `Masker`, provider interface, `ResponseValidator`, `Restorer`, and `PrivacyGateway`. Longest matches win overlaps; equal lengths use EMAIL, ASSET, TICKET, then NAME priority. Missing policies default to MASK. REMOVE deletes a value without creating a restorable token.

`RequestMapping` exists for one `process()` call and is cleared in `finally`, including provider and validation failures. Providers receive only masked/removed text. Timeouts, provider exceptions, malformed responses, and invalid placeholders become controlled errors; there is no unmasked retry.

## Python programming-language design

**Types and contracts:** Frozen dataclasses (`Match`, `PolicyDecision`, `GatewayResult`, and evaluation result types) make data shapes explicit. `Policy` limits policy states to MASK and REMOVE. The provider `Protocol` defines `summarize(masked_ticket, prompt_version)`. Runtime checks protect JSON and provider boundaries. Evidence: CLI boundary and invalid-prompt tests.

**State lifetime:** `RequestMapping` owns placeholder values for one request. `PrivacyGateway.process()` creates it locally and closes it in `finally`. Evidence: mapping-cleanup, independent-request, and reused-request-ID tests.

**Effects:** File loading, standard input/output, and provider calls are isolated from deterministic transformations. Evidence: provider call-count tests and byte-identical repeated evaluation runs.

**Interfaces:** Provider and mapping factories are injected into `PrivacyGateway`. Evidence: `FixedProvider`, `RaisingProvider`, and `CapturingFactory` in `tests/test_gateway.py`.

**Error handling:** Components raise `GatewayError` with stable codes including `INVALID_POLICY`, `INVALID_PLACEHOLDER`, `MALFORMED_RESPONSE`, `PROVIDER_TIMEOUT`, and `PROVIDER_ERROR`. Evidence: invalid-policy, malformed-response, timeout, provider-error, and CLI tests.

## Data flow and trust boundary

```text
LOCAL MACHINE                                         EXTERNAL/PROVIDER SIDE

Synthetic ticket
      |
      v
Detector -> masker -> masked request -------------------> provider/mock
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

Only the masked ticket and versioned task prompt may cross the boundary. Detection rules, detection results, original values, placeholder mappings, validation results, and restored output stay local. The response must be validated before restoration.

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| Input layer | Read one synthetic ticket for one request |
| Detector | Find explainable exact-list and structured-pattern matches |
| Masker | Replace selected spans and create the request-local mapping |
| Provider interface | Send only masked content to the offline mock |
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
[[g8fa21c:NAME:1]]
[[g8fa21c:EMAIL:1]]
[[g8fa21c:ASSET:1]]
[[g8fa21c:TICKET:1]]
```

The gateway generates a fresh opaque namespace for each invocation rather than embedding the caller's request ID. This prevents request-ID leaks and stale-token collisions when IDs are reused. The category and index remain explainable, and repeated occurrences reuse one token. Reserved placeholder syntax in input is rejected.

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
- Exact command executed from the repository root: `& 'C:\Users\gruss\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' src/tech_spike.py`
- Synthetic input: `Ticket INC-1042 reports a Wi-Fi problem.`
- Observed output: `Echo: Ticket INC-1042 reports a Wi-Fi problem.`

The spike does not detect, mask, send, validate, or restore information.

## Initial design decisions

1. Use a local synthetic name list instead of general named-entity recognition so matches are explainable and reproducible.
2. Use request-scoped placeholders containing a request ID to support later authorization checks.
3. Treat the prompt as task guidance and local validation as the enforcement mechanism.
4. Use an offline deterministic mock provider for reproducible gateway tests.

## M2 execution trace

For request `r10`, the synthetic input

```text
Maya Chen cannot connect LT-48291 to Wi-Fi. Ticket INC-1042.
```

is masked locally as

```text
[[r10:NAME:1]] cannot connect [[r10:ASSET:1]] to Wi-Fi. Ticket [[r10:TICKET:1]].
```

The mock provider receives only the masked form. After the response tokens pass validation, the gateway restores `Maya Chen`, `LT-48291`, and `INC-1042` in the final local output.
