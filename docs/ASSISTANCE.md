# Assistance Record


## M1 — Placeholder design

**Source:** ChatGPT-5.6, Sol Light, planning discussion on September 8, 2026.

**Suggestion:** Use placeholders containing a request ID, category, and number, such as `[[r7:NAME:1]]`.

**My decision:** Accepted. The request ID should help identify placeholders from another request, and the number distinguishes different names in one ticket.

**How I checked it:** I compared the format with my planned cases for repeated names and invalid placeholders. This was a design check; the gateway has not been implemented or tested yet.

**Limitation:** The format alone does not make an AI response safe. My code will still need to validate returned placeholders.

## M2 validation assistance: malformed placeholders

**Source:** ChatGPT/Codex, October 15, 2026.

**Suggestion:** Validate incomplete reserved syntax, such as [[r5:NAME:1]], in addition to complete but unknown placeholders such as [[r5:NAME:99]].

**My decision:** Accepted. The validator now rejects malformed bracket syntax with the controlled error code INVALID_PLACEHOLDER.

**How I checked it:** I added an automated test that makes the mock provider return a placeholder with a missing closing bracket. The test confirms that the gateway raises a controlled GatewayError instead of restoring or returning the unsafe response.

**Limitation:** The M2 validator handles the documented placeholder forms and tested malformed examples. Broader adversarial testing belongs to later refinement work.

## Recordkeeping note

Future important assistance from AI, peers, libraries, or other sources will be recorded here with the suggestion, the project decision, and the evidence used to check it.
