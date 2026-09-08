# VIGIL rehearsal schema and mapping decisions

## Security-event stream: `logs-vigil-security`

| Field | Example | Reason |
|---|---|---|
| `@timestamp` | `2026-09-06T08:30:00Z` | Orders the evidence timeline and reporting anchors. |
| `event.kind` | `event` | Standard event classification; ensured by ingest pipeline. |
| `event.category` / `event.type` | `web` / `access` | Uses ECS allowed categorization values; UPI API calls are web access events, not a non-ECS `api` category. |
| `event.action` / `event.outcome` | `login` / `failure` | Drives the transparent alert query and evidence explanation. |
| `host.name` | `pay-svc-prod-01` | Join key to bank context. |
| `user.name`, `source.ip`, `destination.ip` | synthetic identifiers | Evidence context; never real identities or customer addresses. |
| `transaction.id`, `http.*`, `url.path` | `UPI-HERO-001`, `POST`, `/payments/upi/transfer` | Standard ECS transaction and HTTP request context for the fabricated payment API call. |
| `vigil.transaction.amount`, `vigil.transaction.currency`, `vigil.transaction.channel`, `vigil.transaction.profile` | `175000`, `INR`, `UPI`, `outside_normal_batch` | VIGIL-namespaced synthetic payment fixture detail; this is not claimed as an ECS payment schema. |
| `vigil.bank.account_id`, `vigil.bank.upi_vpa` | `ACC-CORP-4417`, `payroll.apex@upi` | Beneficiary identity for the affected-account count. Synthetic; no real VPA or account exists. |
| `vigil.bank.customer_tier` | `Corporate`, `HNI`, `Retail` | Segments the blast radius. Typed `keyword` so it can be grouped in ES\|QL. |
| `vigil.bank.kyc_verified` | `false` | Whether the beneficiary account has completed KYC. Drives rule 05 as a control exception in its own right. Synthetic flag, not a CKYC registry lookup. |
| `vigil.bank.aml_risk_score` | `91.2` | Upstream AML risk score, 0–100, typed `float` so range predicates work. Drives rule 04. Synthetic; not a production AML engine output. |
| `vigil.bank.batch_id` | `UPI-BATCH-20260906-0841` | Groups a settlement batch. Typed `keyword` for aggregation. |
| `event.created`, `event.ingested` | timestamps | Distinguishes first observation by the source/pipeline from Elasticsearch ingestion time. |
| `tags` | `vigil_hero`, `vigil_decoy`, `vigil_rehearsal` | Deterministic scenario selection and ingest provenance. |
| `labels.dataset`, `labels.synthetic` | `vigil-synthetic`, `true` | Makes synthetic origin visible in every event. |

## Namespace decision: why `vigil.bank.*` and not `bank.*`

ECS reserves the top-level field namespace. Custom fields therefore sit behind a vendor
prefix, `vigil.*`, for two reasons that matter under questioning:

1. **Collision safety.** A future ECS release can introduce a top-level `bank.*` set with
   different types. Anything already sitting there would then conflict on upgrade. A vendor
   prefix cannot collide.
2. **Honest labelling.** A reader can tell at a glance which fields are ECS and which are
   ours. A bare `bank.*` implies an ECS field set that does not exist.

`tests/test_contract.py::test_bank_fields_live_under_the_vendor_namespace` asserts that no
event carries a top-level `bank` object, so this cannot regress silently.

## Mapping decisions: why the data stream is explicitly mapped

`elastic/mappings/logs-vigil-security-template.json` is a composable index template installed
**before** the data stream is created. It is not decoration:

- Dynamic mapping types a string as `text` with a `.keyword` subfield. `text` cannot be used
  in an ES\|QL `STATS ... BY` clause and cannot back a threshold rule's grouping field, so
  `vigil.bank.customer_tier`, `batch_id`, `account_id` and `upi_vpa` are declared `keyword`.
- `vigil.bank.aml_risk_score` is `float` so `>= 85` is a range predicate rather than a string
  comparison.
- `vigil.bank.kyc_verified` is `boolean` so `kyc_verified: false` matches the absent-KYC case
  and not the string `"false"`.
- `vigil.transaction.amount` is `long`, not a floating type: rupee amounts must not accumulate
  floating-point drift when summed for a regulatory figure.
- `dynamic: strict` makes an unmapped field a loud ingest failure instead of a silently
  untyped field that breaks a query later.
- `index.default_pipeline` binds `vigil-normalize` to the stream, so normalisation applies to
  any write path, not only the seed script's explicit `?pipeline=` parameter.

## Bank-context lookup index: `vigil-bank-context`

This index uses Elasticsearch `index.mode: lookup`. It contains only two synthetic service records. `host.name` is the join key. `vigil.bank.exposure_inr` and `vigil.bank.account_count` are fixed fixture context, not a real loss model.

It also carries the per-service control context the detection rules are tuned against:
`vigil.bank.aml_alert_threshold` (85.0), `vigil.bank.kyc_required`, `vigil.bank.criticality`
and `vigil.bank.regulated_channel`. Keeping the threshold in the lookup index rather than
inside the rule is deliberate: a real bank tunes it per service, and a judge can see the
number the rule is compared against. The mapping is `dynamic: strict`, so a new context field
requires a mapping change rather than appearing untyped.

## Corpus volume

The corpus is 196 events by default: 120 routine credential refreshes, 60 benign scheduled
settlement transfers (2/day over 30 days), the 12-event hero incident, and the 4-event benign
decoy. `python3 data/generator/generate.py --volume N` scales **only** the benign settlement
background; the hero and decoy event ids, amounts and account set are fixed literals, so the
exposure figure, the dashboard panels and the eval harness stay reproducible at any volume.
This is a rehearsal corpus sized for a reproducible demo. It is not a throughput claim, and
the problem statement's "tens of thousands of alerts a day" is a description of the target
production problem, not of this corpus.

## Retrieval decision

The ES|QL query pivots from the alert's host, user and 15-minute time window, then performs `LOOKUP JOIN vigil-bank-context ON host.name`. It never queries the hidden `vigil_hero` ground-truth tag. This keeps evidence filtering in the security stream and ownership/exposure context in the lookup index. The query returns evidence count, suspicious UPI total, deterministic exposure, affected-account count, service, tier, and owner.

## Event ingestion

`elastic/ingest/vigil-normalize.json` enforces three visible properties on live seed:

1. `labels.dataset = vigil-synthetic` if absent;
2. `vigil_rehearsal` is appended to tags; and
3. `event.kind = event` if absent;
4. `event.dataset = vigil.synthetic`, `ecs.version = 9.5.0`, and pipeline ingestion time are recorded.

The seed script uses that pipeline during bulk ingestion. `make verify-ingest` is the acceptance check.
