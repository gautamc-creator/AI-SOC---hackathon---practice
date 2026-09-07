# VIGIL rehearsal plan → event build plan

## Objective

Arrive at the 18–19 September hackathon able to recreate, explain, test, and present one complete, reliable path. This practice repository is not final event code.

## Complete rehearsal scope

| Layer | Rehearsal acceptance proof |
|---|---|
| Data arrival | Synthetic, ECS-like events land in `logs-vigil-security` through the `vigil-normalize` ingest pipeline. |
| Detection | Two threshold rules and one EQL sequence rule detect behavior without querying the `vigil_hero` ground-truth tag. |
| AI investigation | Elastic Attack Discovery runs against those alerts and is described only as a potential attack discovery. |
| AI claim safety | A deterministic check flags unsupported certainty/attribution in the generated narrative without pretending to decide the incident. |
| Retrieval and impact | ES|QL `LOOKUP JOIN` returns the host, evidence count, affected accounts and deterministic ₹ exposure. |
| Decision | An explicit `approve` / `hold` / `reject` record is produced; no containment is executed. |
| Compliance support | A DAKSH information pack, a CERT-In public-form-aligned draft, and optional STIX 2.1 draft say `NOT SUBMITTED`; none claims to be a portal submission format. |
| Evidence | A hash-chain verifier passes on the original ledger and fails after alteration. |
| UX | The offline War Room shows the evidence, AI interpretation, decision gate and artifacts without a network dependency. |
| Case handoff | A live Elastic Security case contains the synthetic finding and all three component alerts. |
| Native dashboard | A typed Elastic 9.6 dashboard shows three verified ES\|QL evidence metrics and the 16-minute timeline. |
| Human gate | The workflow contains `approve` / `hold` / `reject`; a controlled native gate pauses and resumes with `hold`. |

## What is already proven

- 136 synthetic events, three final Elastic Security alerts and three internal EQL building blocks were observed. Building blocks are excluded from Attack Discovery.
- The ES|QL lookup join returned ₹1,160,000 potential exposure and five affected accounts for the fixed scenario.
- One fresh live Attack Discovery run used all three final alerts and produced one potential discovery through the preconfigured Elastic connector. It is **not an AWS Bedrock demonstration**.
- The AI claim-safety review flagged five phrases that overstated certainty or attribution, and a live Elastic Security case attached all three component alerts.
- The human-gated Elastic Workflow validates and is saved disabled. A constrained Agent Builder evidence-gap test completed in 34,375 ms, and the native decision harness paused, accepted `hold`, and resumed. The complete alert-triggered chain remains unproven.
- The supported Elastic 9.6 typed dashboard renders 12 correlated events, INR 1,160,000 fixture total, five affected accounts and the incident timeline without API warnings.
- The local Golden Path and contract tests pass.
- `make verify-ingest` checks live that all 136 synthetic events received the ingest-pipeline enrichment tags.

## Remaining rehearsal gates

1. Record screenshots of the proven data stream, ingest pipeline, three rules, one Attack Discovery, ES|QL result and live Security case.
2. Configure an AWS Bedrock inference integration only if account access is granted. Do not rename the current baseline or imply it is Bedrock.
3. Prove one complete workflow execution before enabling or attaching the workflow to a rule. Until then, demonstrate the separately proven components and label that boundary.
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
