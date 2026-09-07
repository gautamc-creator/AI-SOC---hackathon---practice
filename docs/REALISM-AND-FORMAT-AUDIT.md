# VIGIL realism and format audit

Reviewed: 7 September 2026. This is the source of truth for what VIGIL does and does **not** claim about real-world formats.

## 1. Event telemetry: aligned to Elastic Common Schema

VIGIL uses ECS as the common telemetry model, not a fictional bank-log schema. ECS exists to normalize logs/metrics in Elasticsearch, specifies field names and datatypes, and supports correlation across sources. [Elastic ECS reference](https://www.elastic.co/docs/reference/ecs) | [Elastic ECS ingestion guidance](https://www.elastic.co/docs/reference/ecs/ecs-getting-started)

| VIGIL data | Real-world alignment | Boundary |
|---|---|---|
| `@timestamp` | Time the source event occurred. | Synthetic timestamp. |
| `event.created` | ECS defines this as when an agent/pipeline first read the event. | Synthetic +2-second fixture delay; not a measured agent latency. |
| `event.ingested` | Set by the Elasticsearch ingest pipeline. | It is observed only in the rehearsal project. |
| `event.kind`, `event.category`, `event.type`, `event.action`, `event.outcome` | ECS categorisation fields. VIGIL uses allowed categories `authentication`, `network`, and `web`, plus allowed types `start`, `connection`, and `access`. | `upi_transfer` is a VIGIL action value, not a universal payment standard. |
| `host.*`, `service.*`, `user.*`, `source.*`, `destination.*`, `related.*` | Standard ECS field sets. ECS recommends source/destination as the baseline for network events and `related.*` for pivots. | Values are documentation/test addresses and synthetic service names. |
| `transaction.id`, `http.*`, `url.path` | Standard ECS transaction and HTTP request context for the synthetic payment API call. | It is still a fabricated API event, not an NPCI payload. |
| `vigil.transaction.*`, `vigil.bank.*` | Namespaced custom fields for bank-specific amount/profile/context, deliberately separate from ECS. | These are VIGIL fixture fields, not an NPCI/UPI message specification or bank loss model. |

The event field choices follow Elastic guidance that normalization usually maps source data into ECS and uses fixed categorization values based on the source type. [ECS event fields](https://www.elastic.co/docs/reference/ecs/ecs-event) | [ECS network mapping](https://www.elastic.co/docs/reference/ecs/ecs-mapping-network-events)

## 2. Synthetic corpus: valid for a prototype, never disguised as real

The corpus is deterministic, local, and labelled `labels.synthetic: true` and `labels.dataset: vigil-synthetic` on every event. A benign maintenance decoy is included so the demo does not equate a failed login with an incident. See [data provenance](../data/DATA-PROVENANCE.md) and [schema decisions](../data/SCHEMA.md).

The live acceptance proof is `make verify-ingest`, which confirms the Elasticsearch ingest pipeline enriched all 136 synthetic records. This proves pipeline behavior, not production detection quality, false-positive rate, or fraud loss.

## 3. CERT-In artifact: public-form-aligned draft

The official CERT-In Incident Reporting Form requests reporter contact, affected entity, incident type, whether the system is mission critical, affected-system information, occurrence/detection time, description, and technical details. It says the form is general guidance, does not need to be completed/signed for every incident, and information can be supplied in another readable form. [CERT-In Incident Reporting Form](https://www.cert-in.org.in/PDF/certinirform.pdf)

`cert-in-incident-form-draft.json` mirrors those information groups. It intentionally leaves reporter/organisation/contact values as `REQUIRED BEFORE SUBMISSION`; VIGIL must never manufacture them. It distinguishes occurrence start from first observation and marks all values synthetic.

CERT-In says an incident is reported within six hours of noticing or being brought to notice, and permits available information first with later updates. [CERT-In FAQ, Q24 and Q30](https://www.cert-in.org.in/PDF/FAQs_on_CyberSecurityDirections_May2022.pdf) | [Current CERT-In reporting page](https://cert-in.org.in/SecurityIncident.jsp)

## 4. RBI artifact: information pack, not a universal submission format

RBI obligations and workflows depend on the regulated entity. RBI's 2024 Master Directions for authorised **non-bank PSOs** require unusual incidents to be reported to RBI in the Incident Reporting Format within six hours of detection and also reported to CERT-In. [RBI Master Directions for non-bank PSOs](https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12715%281%29.html)

DAKSH also hosts payment-fraud reporting for applicable PSOs/providers/participants, with both bulk and screen-based reporting. [RBI CPFIR → DAKSH migration notice](https://rbi.org.in/scripts/NotificationUser.aspx?Id=12431)

VIGIL therefore produces `rbi-daksh-information-pack.json`, **not** an “Annex 1 compatible” file or a DAKSH-upload claim. The final build must identify the actual entity type and have an authorised compliance owner map fields to the current RBI workflow.

## 5. STIX artifact: optional interoperability draft

STIX 2.1 supports bundle, indicator, observed-data, and cyber-observable objects; a bundle transports STIX objects. [OASIS STIX 2.1 specification](https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.pdf)

VIGIL's STIX draft includes a syntactically shaped IPv4 observable, observed-data object, and indicator for the synthetic documentation address. It is **not** a claim that CERT-In requires STIX/TAXII, that a recipient accepts it, or that a draft has passed external validation. Validate it with a STIX validator and recipient-specific guidance before use.

## 6. Stage-safe claims

Safe:

- “Our synthetic telemetry is ECS-aligned and passes a live ingest-pipeline verification.”
- “The CERT-In draft mirrors the public form’s information groups but leaves real reporter fields to an authorised reviewer.”
- “The RBI output is an information pack, not a submitted DAKSH record.”
- “The STIX output is an optional interoperability draft.”

Do not say:

- “These are actual UPI/NPCI message records.”
- “VIGIL can submit to RBI or CERT-In.”
- “This artifact is an RBI upload format.”
- “CERT-In requires STIX/TAXII.”
- “The synthetic exposure is a validated fraud-loss estimate.”
