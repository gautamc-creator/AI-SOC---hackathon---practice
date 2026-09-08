# VIGIL adversarial test plan

How does an AI SOC tool defend its own reasoning path? `tests/test_adversarial.py`
covers everything that is fairly testable offline. Two items are not fakeable
as local unit tests and are documented here as a manual live-environment
procedure instead — a judge asking about them should get "here is exactly how
we tested it," not a fabricated green checkmark.

## Covered by `tests/test_adversarial.py` (run with `make test-adversarial`)

| Threat | Test | What it proves |
|---|---|---|
| Prompt injection inside log messages | `PromptInjectionTests` | Deterministic exposure/escalation fields are identical between the clean hero chain and an event-for-event copy whose messages carry injection text; `workflow/scan_for_injection.py` flags the injected scenario and not the clean one. |
| Fabricated amounts in generated prose | `test_fabricated_amount_in_message_is_ignored_by_exposure_calculation` | Appending a fake loss figure to every message does not move the computed exposure; only the structured `vigil.transaction.amount` field feeds the calculation. |
| Missing events (evidence gap) | `test_missing_transaction_telemetry_reports_insufficient_not_zero` | A scenario with no transaction telemetry reports `INSUFFICIENT_EVIDENCE`, never a fabricated `0`. |
| Duplicated events | `test_duplicate_transactions_are_deduplicated_by_transaction_id` | Repeated transaction ids are counted once for exposure and are surfaced explicitly in `duplicate_transaction_ids`. |
| Malformed timestamps | `test_malformed_timestamp_is_quarantined_not_silently_miscounted` | A corrupted `@timestamp` is quarantined and listed, not silently miscounted into or out of a sequence rule; evaluation completes rather than crashing the whole batch. |
| Cross-incident evidence contamination | `CrossIncidentIsolationTests` | Two scenarios that deliberately share the same host and user do not contaminate each other's evidence set when pooled, because evidence is scoped by explicit event id, not by a host/user query (which this test shows would wrongly merge them). |
| Ledger reordering | `test_reordered_blocks_are_detected` | Swapping two blocks breaks the hash chain and is caught. |
| Ledger deletion | `test_deleted_block_is_detected` | Removing a block breaks the following block's `previous_hash` link and is caught. |
| Forged block content | `test_forged_block_with_fabricated_hash_is_detected` | Changing a block's payload without recomputing its hash is caught. |

## Requires a live Elastic environment — manual procedure, not automated here

### Unauthorized workflow resumption

**Threat:** could a decision payload meant for one case's `waitForInput` human
gate (`elastic/workflows/vigil-human-gated-triage.yaml`, step `human_decision`)
be replayed against a *different* case's execution, or resumed twice?

**Why it's not a local unit test:** this depends on how Elastic Workflows'
resumption API actually authorizes a resume call against a specific execution
id — that is live platform behavior this repository has not yet exercised
adversarially, and faking it locally would just test an assumption about the
API, not the API itself.

**Manual procedure (run only against the disabled/isolated workflow, never
mid-rehearsal on the live demo path):**
1. Start two separate workflow executions (e.g. by running
   `make workflow-e2e-test` twice, or the case-based trigger twice), so two
   `human_decision` `waitForInput` steps are pending concurrently.
2. Attempt to POST execution A's decision payload against execution B's
   resume endpoint/case id.
3. Attempt to resume the same execution twice with two different decisions
   (`approve` then `reject`).
4. Expected result: the platform must reject a mismatched execution/case id
   and must not allow a second resume to silently overwrite the first
   recorded decision. Record whatever actually happens — pass or fail — in
   `presentation/EVENT-DAY-BUILD-LOG.md`, not as an assumed pass.

### Live ledger tamper detection end-to-end

`tests/test_adversarial.py::LedgerTamperTests` proves the chain math catches
reordering/deletion/forgery in isolation. `scripts/golden_path.py` already
proves the end-to-end genuine-vs-tampered case for the one frozen ledger file.
Repeating that specific end-to-end proof for each of the eight eval scenarios
is unnecessary — the chain algorithm is scenario-independent — so it is not
duplicated here.
