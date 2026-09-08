# VIGIL claim register — judge-facing use only

Updated: 8 September 2026

This is the source of truth for the rehearsal deck and stage script. A claim not listed as **safe** must not be presented as a result.

## Safe, directly demonstrated

| Claim | Evidence |
|---|---|
| The rehearsal used Elastic/Kibana 9.6.0. | Live deployment version check. |
| 196 seeded, synthetic events were ingested and normalized with the `vigil-normalize` pipeline. | Fresh live validation required after the corpus change — **re-run `make seed && make verify-ingest` before claiming this number live.** |
| Three final behaviour-based alerts and three EQL building-block alerts were generated. | Detection API validation; building blocks are excluded from the final-alert count. **Rules 04 and 05 were added on 8 September and have not yet been validated live; do not include them in an alert count until `make validate-alerts` has run against the reseeded deployment.** |
| Five detection rules exist and none pins a host, address, user or account literal. | `tests/test_contract.py::test_rule_queries_contain_no_hardcoded_indicator` asserts it; the AML rule matches on `vigil.bank.aml_risk_score >= 85`. |
| The AML score separates the hero incident from routine settlement traffic with no overlap. | Hero scores 88.7–94.5, benign settlement 0.5–8.0, service threshold 85.0. Asserted by `test_bank_enrichment_is_typed_and_separates_hero_from_benign`. |
| The benign decoy is excluded by falling below the threshold, not by being named. | Rule 01 names no user; the decoy's 4 failed logins sit under the threshold of 5. |
| The data stream is created from an explicit composable index template with `dynamic: strict`. | `elastic/mappings/logs-vigil-security-template.json`, installed by `elastic/seed.py` before the stream. |
| Bank-domain fields sit under `vigil.bank.*`, never a bare top-level `bank.*`. | ECS reserves the top level. Asserted by `test_bank_fields_live_under_the_vendor_namespace`. |
| Attack Discovery produced one potential discovery from three final alerts. | Private rehearsal execution evidence retained locally; identifiers are not published. |
| An ES\|QL evidence pivot returned 12 correlated events, ₹11,60,000 of suspicious UPI fixture value, and five affected accounts. | Saved VIGIL dashboard and live query. These are scenario facts, not loss estimates. |
| The AI narrative contained five unsupported-certainty phrases and was held for review. | Deterministic guardrail output from `workflow/review_discovery.py`. |
| A full workflow created a case, attached three alerts, invoked an Elastic Agent Builder agent, paused for human input, resumed with `hold`, and completed. | Private rehearsal execution and case evidence retained locally; identifiers are not published. |
| The local evidence ledger contains seven linked blocks; verification passes on the genuine ledger and fails on a tampered copy. | `make demo`. |
| The War Room re-verifies the ledger in the browser with Web Crypto, recomputing each block's digest from its canonical bytes rather than trusting the stored hash. | `warroom/index.html`; the page runs a visible canonicaliser self-test and reproduces all seven stored digests, including the two blocks containing non-ASCII characters. |
| Altering one sealed value in the browser breaks that block and every block after it. | The "Alter one evidence value" control changes `amount_inr` and re-runs verification client-side. |
| Twenty-eight automated tests pass; one live-environment workflow authorization test is explicitly skipped locally. | `make test` (29 discovered). |
| The static War Room deploys with no server, no credential and no live cluster address. | `make site` stages 18 published artifacts and scans every staged file for each value in `.env` and for AWS/PEM/endpoint credential shapes, refusing to publish on a hit. |
| Sarvam AI translated the incident brief into Hindi, Marathi, Tamil, Telugu and Bengali, and the ₹11,60,000 magnitude survived all five translations. | Live `/translate` capture in `artifacts/indic-localisation.json` on 8 September 2026; `status: CAPTURED` and five `MAGNITUDE_PRESERVED` checks. The English draft remains authoritative. |

## Safe, directly verified from primary sources

| Claim | Source-backed wording |
|---|---|
| CERT-In requires covered entities to report listed cyber incidents within six hours of noticing or being brought to notice. | CERT-In Directions No. 20(3)/2022-CERT-In, direction (ii). |
| CERT-In Annexure I includes unauthorized access and incidents affecting digital-payment systems. | Same Directions, Annexure I. |
| The CERT-In Incident Reporting Form is guidance and is not mandatory to fill or sign. | Note (ii) on the official form. |
| The RBI 2026 commercial-bank Directions require covered banks to report cyber incidents on DAKSH within six hours of detection and proactively notify CERT-In. | RBI Notification 13643. Avoid extending this commercial-bank instrument to excluded bank classes. |
| Elastic Workflows support `waitForInput` / `waitForApproval`, and Elastic Agent Builder agents can be called from workflows with `ai.agent`. | Current Elastic documentation. |

## Must be qualified

| Topic | Required wording |
|---|---|
| Data | “Seeded synthetic rehearsal data, ECS-aligned with a bank-specific namespace.” Do not call it production bank data or NPCI wire-format data. |
| ₹11,60,000 | “Suspicious UPI fixture value linked by the scenario.” It is not proven fraud, loss, or exposure avoided. |
| Attack Discovery | “Potential discovery” or “AI lead.” Never “validated attack,” “confirmed fraud,” or “attacker.” |
| Regulatory artifact | “Human-review draft compatible with CERT-In form fields plus a DAKSH preparation pack.” It is not an official filing and is never submitted automatically. |
| Containment | “Simulated/logged decision.” No host isolation, token revocation, payment freeze, or external notification is executed. |
| Performance | The local deterministic median excludes Elastic, LLM, network, and UI time. Do not use it as end-to-end latency or an SLO. |
| AWS LLM | Current rehearsal AI used an Elastic preconfigured managed connector. An AWS Bedrock path is now **implemented** (`llm/bedrock.py`, stdlib SigV4, Converse API, model auto-discovery) but **not yet demonstrated**: say "implemented, pending a captured run", never "we use Bedrock", until `make bedrock-probe` and `make brief-live` have succeeded and `artifacts/bedrock-grounded-brief.json` shows `status: CAPTURED`. The artifact records the real model id, so the claim is whatever the artifact says and nothing more. |
| Bedrock model | `apac.amazon.nova-micro-v1:0` is the selected non-Anthropic profile. A live probe reached Bedrock but AWS account verification blocked invocation, so the integration remains implemented but not demonstrated until the brief artifact says `CAPTURED`. |
| Sarvam AI | “Five live Indic translations captured; rupee magnitude preserved in all five.” Treat them as an internal readability aid. The English incident draft remains authoritative, and Sarvam establishes no incident fact. |
| Ungrounded-claim check | "A grounding check on financial magnitudes, IPv4 literals and transaction ids against the sealed evidence set." It is not a semantic fact checker and does not adjudicate whether an incident occurred. |
| MITRE techniques | "Mapped deterministically by VIGIL from corpus tags and event actions." Attack Discovery named three tactics; VIGIL's evidence mapping supports four. Do not present the technique mapping as an AI conclusion. |
| Escalation payloads | "Schema-valid preview bodies built from the artifacts." VIGIL holds no Slack, PagerDuty or Jira credential and makes no network call. The Elastic webhook connector is a definition only and was not created. |
| Corpus size | "196 synthetic events, of which 60 are benign settlement background, scalable with `--volume`." Never present it as production throughput or as the "tens of thousands of alerts a day" in the problem statement. |

## Remove from all judge-facing material

- 45 minutes to 4.2 minutes, 90% faster, 95% reduction, 60% false-positive reduction.
- 50,000+ alerts per day, four hours of paperwork, or any other unsourced industry-volume figure.
- 100% audit-proof, zero hallucination, zero breaches, or guaranteed compliance.
- A ₹5 lakh RBI reporting threshold, “RBI Section 4.2,” or a ₹1 crore penalty avoided.
- “Official CERT-In Annexure-1 PDF.” Annexure I is the incident-type list; the separate Incident Reporting Form is non-mandatory guidance.
- S3 Object Lock, KMS signing, or WORM storage in any form. Nothing in VIGIL writes to object storage or signs with a KMS key, and the ledger is a tamper-evident hash chain, not immutable storage.
- AWS Bedrock as **already demonstrated**, or Sarvam as establishing incident facts/data-localisation compliance. Bedrock invocation is pending AWS account verification. Sarvam translation is demonstrated, but only as a five-language internal readability aid over an English authoritative draft.
- "Merkle tree" or "Merkle chain." The ledger is a linear SHA-256 hash chain; calling it a Merkle tree is wrong and invites a question that ends badly.
- "Autonomous threat hunting with no hardcoded indicators" as an absolute. The correct claim is narrower and defensible: no rule query pins a host, address, user or account literal, and a test asserts it.
- Any claim that candidate rules 06 and 07 are live-proven. Their local predicate mirrors close the m2 insider-KYC and m3 duplicate-settlement evaluation gaps, but the Elastic rules stay disabled until replayed in an isolated live evaluation index.
- A per-language count for Indic briefs that is larger than the number of languages actually captured in the artifact.
- STIX/TAXII as the CERT-In incident-report submission format. STIX/TAXII may be useful for threat-intelligence exchange, but it is not the public incident-reporting form contract.
