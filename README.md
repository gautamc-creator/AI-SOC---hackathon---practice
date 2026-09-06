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
2. **Detect and investigate:** a custom Elastic Security rule creates alerts; Elastic Attack Discovery can generate a *potential* investigation lead.
3. **Ground the impact:** ES|QL `LOOKUP JOIN` connects the host to synthetic bank context and calculates exposure deterministically.
4. **Decide:** the analyst records `approve`, `hold`, or `reject`; this demonstration records intent only and never contains a system.
5. **Prepare:** VIGIL produces human-review-only RBI DAKSH, CERT-In and optional STIX 2.1 drafts.
6. **Prove:** a SHA-256 evidence ledger is independently verified; the Golden Path also proves tampering is detected.
7. **Present:** `make warroom`, then run `python3 -m http.server 8000` at repository root and open `http://localhost:8000/warroom/`.

## Live Elastic gate

After the local run passes, follow [docs/ELASTIC-CHECKLIST.md](docs/ELASTIC-CHECKLIST.md). The live demonstration is not complete until it shows:

1. the synthetic data in Elasticsearch;
2. a real alert and Attack Discovery output using the configured LLM connection, labelled accurately as Bedrock-backed only after Bedrock is actually configured;
3. the saved ES|QL lookup join; and
4. the local human-review draft and passing/failing ledger verification.

## Key limitations

- Synthetic data only; the rupee amount is deterministic fixture context, not a production risk calculation.
- Attack Discovery produces a potential discovery, not a guaranteed validated incident.
- The CERT-In-compatible / RBI DAKSH artifact is a draft for human review. VIGIL never files with a regulator.
- The local ledger is SHA-256 hash chained. S3 Object Lock and KMS signing are intentional future enhancements.
- The STIX JSON is an interoperability draft, not a statement that a recipient currently requires or accepts it.
