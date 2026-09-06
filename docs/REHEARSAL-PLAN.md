# VIGIL rehearsal plan → event build plan

## Objective

Arrive at the 18–19 September hackathon able to recreate, explain, test, and present one complete, reliable path. This practice repository is not final event code.

## Complete rehearsal scope

| Layer | Rehearsal acceptance proof |
|---|---|
| Data arrival | Synthetic, ECS-like events land in `logs-vigil-security` through the `vigil-normalize` ingest pipeline. |
| Detection | `vigil-synthetic-payment-compromise-v1` creates alerts for the hero sequence. |
| AI investigation | Elastic Attack Discovery runs against those alerts and is described only as a potential attack discovery. |
| Retrieval and impact | ES|QL `LOOKUP JOIN` returns the host, evidence count, affected accounts and deterministic ₹ exposure. |
| Decision | An explicit `approve` / `hold` / `reject` record is produced; no containment is executed. |
| Compliance support | Review-only DAKSH, CERT-In and optional STIX drafts say `NOT SUBMITTED`. |
| Evidence | A hash-chain verifier passes on the original ledger and fails after alteration. |
| UX | The offline War Room shows the evidence, AI interpretation, decision gate and artifacts without a network dependency. |

## What is already proven

- 136 synthetic events and 12 live Elastic Security alerts were observed in the rehearsal project.
- The ES|QL lookup join returned ₹1,160,000 potential exposure and five affected accounts for the fixed scenario.
- One live Attack Discovery run produced one potential discovery through the preconfigured Elastic connector. It is **not an AWS Bedrock demonstration**.
- The local Golden Path and contract tests pass.

## Remaining rehearsal gates

1. Run `make seed`, `make validate`, `make create-rule`, `make validate-alerts`, then capture a fresh Attack Discovery result; record screenshots and observed timings.
2. Configure an AWS Bedrock inference integration only if account access is granted. Do not rename the current baseline or imply it is Bedrock.
3. Build saved Kibana Discover views and one dashboard that demonstrate the data stream, ingest pipeline, alert, ES|QL query and Attack Discovery result.
4. Run three full rehearsals: operator flow, 3–5 minute stage demo, and judge Q&A.
5. Record a backup video only if hackathon rules permit it.

## Event-day rebuild order

1. Create the official repository and write `PRE_EVENT_NOTES.md` describing the rehearsal work honestly.
2. Establish the provided Elastic/AWS/Sarvam environments and record exact product versions/configuration.
3. Recreate ingestion and one detection scenario first; prove alerts before any UI work.
4. Configure and test the sponsor-provided LLM path; retain one real output.
5. Recreate the ES|QL lookup, review artefacts and verifier.
6. Rebuild the War Room / Kibana view using the event environment.
7. Re-run the acceptance table above, polish presentation, and rehearse.

## Scope guardrails

Do not add automatic containment, regulator submission, customer data, unverified statistics, a false Bedrock claim, or a second untested incident scenario. Any added feature must improve one of the five published scoring categories and have a live proof.
