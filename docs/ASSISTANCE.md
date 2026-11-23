# Assistance Record

## AI planning assistance: placeholder format

**Suggestion received:** Include a request identifier, category, and per-category index in each placeholder, for example `[[r7:NAME:1]]`, instead of using generic sequential tokens such as `[[VALUE1]]`.

**Decision:** Accepted. The request identifier will help the validator distinguish a well-formed placeholder issued for the current request from one issued for another request. The category makes traces and validation errors easier to explain. The index distinguishes multiple entities in one category.

**Check performed:** The format was checked against ordinary, repeated-value, invalid-placeholder, reserved-syntax, request-ID leak, and reused-request-ID cases. M3 uses a fresh opaque namespace for each invocation while retaining category and index fields.

**Limitation identified:** A good placeholder format does not make provider output trustworthy. The implementation must still validate every returned placeholder against the current request's local mapping before restoration.

## Recordkeeping note

Future important assistance from AI, peers, libraries, or other sources will be recorded here with the suggestion, the project decision, and the evidence used to check it.

## M2 implementation assistance: component separation

**Suggestion received:** Keep detection, masking, provider behavior, response validation, and restoration in separate classes, with one gateway object coordinating a request.

**Decision:** Accepted. This structure makes the local/external boundary visible and allows invalid provider responses to be tested without changing detection code.

**Check performed:** The M2 checkpoint originally ran eight automated tests covering ordinary input, repeated values, different names, no sensitive data, unknown placeholders, malformed placeholders, foreign-request placeholders, and reserved input syntax.

**Limitation identified:** No separate course JSON I/O Contract exists, so the repository must clearly document and test its own command-line contract.

## M3 planning assistance: policy and request state

**Suggestion received:** Separate overlap resolution, category policy, request mapping, provider behavior, validation, and restoration, and clear request mappings in a `finally` path.

**Decision:** Accepted. The design uses focused components, MASK/REMOVE policy, and one mapping per request.

**Check performed:** Automated tests verify longest-match overlap behavior, policy defaults and errors, mixed MASK/REMOVE requests, independent requests, and mapping cleanup after success and provider failure.

**Limitation identified:** Detection remains rule-based and intentionally narrow; unsupported phone numbers can be missed.

## M3 evaluation assistance: prompt comparison

**Suggestion received:** Compare two prompt versions offline on the same three cases and score required information, format, placeholders, invented information, and usefulness.

**Decision:** Accepted. Prompt v2 adds an explicit output contract, fact requirements, exact placeholder rules, and missing-information behavior.

**Check performed:** The deterministic evaluation produced six mock outputs. Prompt v1 scored 13/15 and v2 scored 15/15 on November 17, 2026; repeated runs were identical.

**Limitation identified:** These are offline mock-provider results, not evidence of real-model quality.
