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
| `vigil.transaction.amount`, `vigil.transaction.currency`, `vigil.transaction.channel` | `175000`, `INR`, `UPI` | VIGIL-namespaced synthetic payment fixture detail; this is not claimed as an ECS payment schema. |
| `event.created`, `event.ingested` | timestamps | Distinguishes first observation by the source/pipeline from Elasticsearch ingestion time. |
| `tags` | `vigil_hero`, `vigil_decoy`, `vigil_rehearsal` | Deterministic scenario selection and ingest provenance. |
| `labels.dataset`, `labels.synthetic` | `vigil-synthetic`, `true` | Makes synthetic origin visible in every event. |

## Bank-context lookup index: `vigil-bank-context`

This index uses Elasticsearch `index.mode: lookup`. It contains only two synthetic service records. `host.name` is the join key. `vigil.bank.exposure_inr` and `vigil.bank.account_count` are fixed fixture context, not a real loss model.

## Retrieval decision

The ES|QL query pivots from the alert's host, user and 15-minute time window, then performs `LOOKUP JOIN vigil-bank-context ON host.name`. It never queries the hidden `vigil_hero` ground-truth tag. This keeps evidence filtering in the security stream and ownership/exposure context in the lookup index. The query returns evidence count, suspicious UPI total, deterministic exposure, affected-account count, service, tier, and owner.

## Event ingestion

`elastic/ingest/vigil-normalize.json` enforces three visible properties on live seed:

1. `labels.dataset = vigil-synthetic` if absent;
2. `vigil_rehearsal` is appended to tags; and
3. `event.kind = event` if absent;
4. `event.dataset = vigil.synthetic`, `ecs.version = 9.5.0`, and pipeline ingestion time are recorded.

The seed script uses that pipeline during bulk ingestion. `make verify-ingest` is the acceptance check.
