# Evaluation

## M1 planned acceptance cases

All examples are synthetic. They were planned during M1 and automated for the M2 prototype.

### AC-01: Ordinary input

**Input**

```text
Maya Chen reports that laptop LT-48291 cannot connect to Wi-Fi after a password reset. Contact maya.chen@example.test. Ticket INC-1042.
```

**Expected outbound properties**

- All four original protected values are absent.
- Four valid placeholders appear for NAME, ASSET, EMAIL, and TICKET.
- The Wi-Fi problem and password-reset context remain readable.

**Expected final properties**

- The summary accurately describes the Wi-Fi problem.
- Relevant placeholders are restored locally.
- No new identifier or unsupported fact appears.

### AC-02: Repeated value

**Input**

```text
Maya Chen cannot sign in. Maya Chen asked for an update at maya.chen@example.test; send the reply to maya.chen@example.test. Ticket INC-1043.
```

**Expected outbound properties**

- Both occurrences of `Maya Chen` use the same NAME placeholder.
- Both occurrences of the email use the same EMAIL placeholder.
- The original name, email, and ticket number are absent.

**Expected final properties**

- Repeated valid placeholders can be restored consistently.
- Repetition does not create conflicting mappings.

### AC-03: No sensitive data

**Input**

```text
The conference-room display shows a blank screen after waking from sleep.
```

**Expected outbound properties**

- The text is unchanged because no supported sensitive value is present.
- No placeholder is created.

**Expected final properties**

- The response remains useful.
- Restoration makes no changes.

### AC-04: Invalid placeholder response

**Input**

```text
Jordan Lee reports that laptop LT-10007 has no audio. Ticket INC-1044.
```

**Simulated provider response**

```text
Summary: [[r7:NAME:99]] reports that [[r7:ASSET:1]] has no audio.
```

**Expected behavior**

- Validation identifies `[[r7:NAME:99]]` as unknown for the request.
- The gateway returns a controlled validation error.
- It does not partially restore the response or return an unmasked fallback.

## Additional automated case

### AC-05: Reserved placeholder syntax in input

**Input**

```text
The ticket text contains [[r7:NAME:1]] as typed content.
```

**Expected behavior**

- The gateway rejects the input with a controlled error before provider processing.
- It does not confuse user text with gateway-issued placeholders.

## Evaluation measures

- Count true positives, false positives, and false negatives for labeled detections.
- Calculate precision and recall when their denominators are nonzero.
- Count each protected-value occurrence remaining in an outbound payload as a leak.
- Record invalid placeholder findings separately from restoration results.
- Evaluate privacy behavior and summary usefulness separately.

## M2 executed test results

The M1 cases are now automated in `tests/test_gateway.py`. The suite also checks different names within one request, a malformed provider placeholder, a foreign-request placeholder, and reserved placeholder syntax in input.

Command:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Observed result on October 15, 2026:

```text
Ran 8 tests
OK
```

The ordinary-input test verifies that each original protected value is absent from the masked outbound text and present after authorized local restoration. The repeated-value test verifies token reuse. Error tests verify that invalid output is rejected rather than partially restored.

These tests use the offline deterministic mock or a fixed invalid response. They are not real-model results.

## M3 automated test results

Command:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Observed November 17, 2026:

```text
Ran 41 tests
OK
```

The expanded suite covers normal and repeated values, different entities, deterministic overlaps, MASK and REMOVE policy, invalid policies, independent requests, mapping cleanup, malformed/unknown/foreign placeholders, malformed responses, provider timeout/error behavior, metrics, leaks, and prompt comparison.

## Detection and privacy results

The labeled synthetic fixture produced:

| Measure | Result |
| --- | ---: |
| True positives | 10 |
| False positives | 1 |
| False negatives | 1 |
| Precision | 0.9091 |
| Recall | 0.9091 |
| Outbound privacy leaks | 1 |

The intentional false positive is an asset-shaped public demo code (`LT-12345`) that the narrow pattern masks. The intentional false negative and leak is an unsupported phone number (`404-555-0100`). This shows the gateway protects supported detections but does not provide universal sensitive-data detection.

## Prompt comparison

Provider kind: **offline deterministic mock**. No real-model results were collected.

The same three masked cases were evaluated with both prompts. Each dimension was scored 0 or 1: required information, output format, placeholder handling, no invented information, and task usefulness.

| Case | v1 | v2 | Observation |
| --- | ---: | ---: | --- |
| Wi-Fi/password reset | 5/5 | 5/5 | Both preserved tokens and required facts. |
| Repeated sign-in values | 5/5 | 5/5 | Both preserved repeated relevant tokens. |
| Sparse display ticket | 3/5 | 5/5 | v1 omitted an explicit missing-context statement; v2 reported `not provided`. |
| **Total** | **13/15** | **15/15** | **v2 selected.** |

Per-dimension scores (`R` required information, `F` format, `P` placeholders, `I` no listed or identifier invention, `U` usefulness):

| Case/version | R | F | P | I | U | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Wi-Fi v1 | 1 | 1 | 1 | 1 | 1 | 5 |
| Sign-in v1 | 1 | 1 | 1 | 1 | 1 | 5 |
| Sparse v1 | 0 | 1 | 1 | 1 | 0 | 3 |
| Wi-Fi v2 | 1 | 1 | 1 | 1 | 1 | 5 |
| Sign-in v2 | 1 | 1 | 1 | 1 | 1 | 5 |
| Sparse v2 | 1 | 1 | 1 | 1 | 1 | 5 |

Complete Wi-Fi and repeated sign-in outputs:

```text
Wi-Fi v1
Summary: [[p1:NAME:1]] cannot connect [[p1:ASSET:1]] to Wi-Fi after a password reset.
Suggested steps:
1. Confirm the reported symptoms.
2. Check relevant device settings.

Wi-Fi v2
Summary: [[p1:NAME:1]] cannot connect [[p1:ASSET:1]] to Wi-Fi after a password reset.
Suggested steps:
1. Confirm the reported symptom and any recent change.
2. Check the affected system settings using only the supplied ticket facts.

Sign-in v1
Summary: [[p2:NAME:1]] cannot sign in. Reply to [[p2:EMAIL:1]] and notify [[p2:NAME:1]] at [[p2:EMAIL:1]].
Suggested steps:
1. Confirm the reported symptoms.
2. Check relevant device settings.

Sign-in v2
Summary: [[p2:NAME:1]] cannot sign in. Reply to [[p2:EMAIL:1]] and notify [[p2:NAME:1]] at [[p2:EMAIL:1]].
Suggested steps:
1. Confirm the reported symptom and any recent change.
2. Check the affected system settings using only the supplied ticket facts.
```

Representative sparse outputs:

```text
v1 Summary: The conference-room display is blank.
Suggested steps:
1. Confirm the reported symptoms.
2. Check relevant device settings.
```

```text
v2 Summary: The conference-room display is blank. Diagnostic context: not provided.
Suggested steps:
1. Confirm the reported symptom and any recent change.
2. Check the affected system settings using only the supplied ticket facts.
```

Prompt v2 performed better because its explicit missing-information rule improved the sparse case while preserving the required format and placeholders. This conclusion applies only to the deterministic mock experiment.

## Remaining limitations

- Exact-name matching only recognizes entries in the local synthetic list.
- Structured patterns can create false positives and miss unsupported formats.
- Prompt scores are rule-based mock results rather than human or real-model evaluation.
- The system is single-turn and command-line only.
