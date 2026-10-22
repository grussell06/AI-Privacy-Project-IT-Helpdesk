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

## Measures reserved for later milestones

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
