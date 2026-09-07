# VIGIL — full rehearsal product

VIGIL is a synthetic banking-SOC rehearsal product. It demonstrates the bank-specific layer after Elastic produces a potential attack discovery: deterministic bank exposure, a human review gate, regulator-ready information drafts, and a tamper-evident evidence ledger.

> **Hackathon integrity:** This repository is a pre-event rehearsal and learning spike. At the event, the selected design will be rebuilt in the official repository and the team will clearly state what was tested before the event versus built during it.

## What works locally now

```bash
make demo
```

This produces a fixed 30-day synthetic corpus containing one compromised payment-service/UPI-batch scenario and one benign maintenance decoy. It creates a clearly labelled draft report, records a simulated analyst hold, creates RBI DAKSH/CERT-In/STIX review drafts, prepares the offline War Room, verifies the genuine evidence ledger, then deliberately alters a copy and proves that verification fails.

Nothing in the local run calls an LLM, contains a system, sends a report, or uses real banking data.

## Rehearsal system map

1. **Ingest:** an Elasticsearch data stream and `vigil-normalize` ingest pipeline process synthetic ECS-like security telemetry.
2. **Classify and gather:** deterministic code creates a preliminary classification and SHA-256 evidence envelope; it makes no LLM or production-model claim.
3. **Detect and investigate:** two threshold rules and one EQL sequence rule create three behavior-based final alerts; Elastic Attack Discovery generates a *potential* investigation lead.
4. **Ground the impact:** ES|QL `LOOKUP JOIN` connects the host to synthetic bank context and calculates exposure deterministically.
5. **Decide:** the analyst records `approve`, `hold`, or `reject`; this demonstration records intent only and never contains a system.
6. **Prepare:** VIGIL produces human-review-only RBI DAKSH, CERT-In, optional STIX 2.1 and notification-preview artifacts. Nothing is sent.
7. **Challenge the AI:** a deterministic claim-safety check flags certainty or attribution that the evidence does not establish. It is a phrase-level guardrail, not a second incident verdict.
8. **Prove and present:** a live Elastic Security case holds the three component alerts; a SHA-256 evidence ledger is independently verified and the Golden Path proves tampering is detected. Run `make warroom`, then `python3 -m http.server 8000` at repository root and open `http://localhost:8000/warroom/`.

The live rehearsal deployment also contains a supported Elastic 9.6 typed dashboard with three ES|QL evidence metrics and a timeline. `make dashboard-live` upserts it and verifies all five panels by reading the dashboard back. `make workflow-agent-test` proves the controlled Agent Builder evidence-gap step; `make workflow-human-gate-test` proves the native three-way decision gate. `make workflow-e2e-test` is an explicitly live, synthetic test: it creates one case, attaches three alerts, runs the constrained agent, pauses for `approve` / `hold` / `reject`, records `hold`, and verifies the case. It has no containment, external notification, or submission step.

Read [data provenance](data/DATA-PROVENANCE.md) and the [field/schema decisions](data/SCHEMA.md) before presenting the corpus. They make the synthetic-data boundary, source, event fields, and live ingest proof explicit.

For the defensible, source-backed answer to “does this look like the real world?”, see the [realism and format audit](docs/REALISM-AND-FORMAT-AUDIT.md). It states exactly which formats are aligned, which are drafts, and which claims are prohibited.

For the evidence mapped to the judging rubric and the remaining build order, see the [judge-readiness audit](docs/JUDGE-READINESS.md).

## Live Elastic gate

After the local run passes, follow [docs/ELASTIC-CHECKLIST.md](docs/ELASTIC-CHECKLIST.md). The live demonstration is not complete until it shows:

1. the synthetic data in Elasticsearch;
2. a real alert and Attack Discovery output using the configured LLM connection, labelled accurately as Bedrock-backed only after Bedrock is actually configured;
3. the saved ES|QL lookup join; and
4. the local human-review draft and passing/failing ledger verification.

Run `make benchmark` only for the local deterministic path. Its output explicitly excludes Elastic/LLM/network latency and must not be presented as a production SLO.

`make workflow-live` validates and saves the human-gated Elastic workflow **disabled**. The complete sequence is proven through a controlled manual test harness, but automatic Attack Discovery alert-trigger attachment is not. Keep the saved trigger disabled until that event binding is tested in the event environment; do not describe the system as autonomously responding.

## Key limitations

- Synthetic data only; the rupee amount is deterministic fixture context, not a production risk calculation.
- Attack Discovery produces a potential discovery, not a guaranteed validated incident.
- The CERT-In-compatible / RBI DAKSH artifact is a draft for human review. VIGIL never files with a regulator.
- The local ledger is SHA-256 hash chained. S3 Object Lock and KMS signing are intentional future enhancements.
- The STIX JSON is an interoperability draft, not a statement that a recipient currently requires or accepts it.
