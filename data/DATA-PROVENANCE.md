# VIGIL rehearsal data provenance

## What this data is

Every event and bank-context record used by VIGIL is generated locally by `generator/generate.py` with a fixed seed (`20260906`). It is **synthetic** and contains no customer, employee, account-holder, production bank, or production security data. The generator is part of this repository; the dataset is reproducible rather than downloaded from an unverified source.

## Why synthetic data is used

The rehearsal demonstrates an incident path involving a payment-service host, privileged access, UPI transfers, and evidence retention. Real data for this type of exercise would be sensitive. Synthetic data lets us demonstrate the schema, security workflow, and evidence boundaries without claiming it represents a real bank or real incident.

## Scenario design

| Scenario | Records | Intended result | Purpose |
|---|---:|---|---|
| Normal payment-service operations | 120 | No VIGIL alert | Provides ordinary background telemetry across 30 days. |
| Credential compromise → UPI transfers | 12 | Potential investigation lead | Five failed privileged logins, one success, outbound connection, and five anomalous UPI transfers totaling ₹1,160,000. |
| Scheduled-maintenance decoy | 4 | No reportable outcome | Failed maintenance logins without egress or transaction impact; tests that a suspicious event does not automatically become a report. |

The `reportable` field in `ground-truth.json` is an internal fixture expectation only. It does **not** determine real-world regulatory reportability.

## Provenance and integrity controls

- Input generation is deterministic: the same seed produces the same corpus.
- Every generated event includes `labels.synthetic: "true"` and `labels.dataset: "vigil-synthetic"`.
- The live ingest pipeline adds `vigil_rehearsal`; `make verify-ingest` confirms this enrichment on all 136 events.
- `ground-truth.json` identifies the designed hero and decoy sets for evaluation; detection rules never query those labels or the `vigil_hero` tag.
- The evidence envelope includes a SHA-256 hash of the selected evidence set. The separate ledger chains later decision/report artifacts and detects tampering.

## External data roadmap

The AMA encouraged real, licensed, moving data where appropriate. VIGIL should add a public threat-intelligence feed only after documenting its publisher, licence, update cadence, and field mapping. It must never add real transaction or personal data for a stage demo. The event build will use only data sources explicitly permitted by the hackathon and their licences.
