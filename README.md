# VIGIL — solo candidate MVP

VIGIL is a synthetic banking-SOC prototype. It demonstrates the bank-specific layer after Elastic produces a potential attack discovery: deterministic bank exposure, a human-review reporting draft, and a tamper-evident evidence ledger.

## What works locally now

```bash
make demo
```

This produces a fixed 30-day synthetic corpus containing one compromised payment-service/UPI-batch scenario and one benign maintenance decoy. It creates a clearly labelled draft report, verifies the genuine evidence ledger, then deliberately alters a copy and proves that verification fails.

Nothing in the local run calls an LLM, sends a report, or uses real banking data.

## Live Elastic gate

After the local run passes, follow [docs/ELASTIC-CHECKLIST.md](docs/ELASTIC-CHECKLIST.md). The live demonstration is not complete until it shows:

1. the synthetic data in Elasticsearch;
2. a real alert and Attack Discovery output using the configured Amazon Bedrock-backed LLM connection;
3. the saved ES|QL lookup join; and
4. the local human-review draft and passing/failing ledger verification.

## Key limitations

- Synthetic data only; the rupee amount is deterministic fixture context, not a production risk calculation.
- Attack Discovery produces a potential discovery, not a guaranteed validated incident.
- The CERT-In-compatible / RBI DAKSH artifact is a draft for human review. VIGIL never files with a regulator.
- The local ledger is SHA-256 hash chained. S3 Object Lock and KMS signing are intentional future enhancements.
