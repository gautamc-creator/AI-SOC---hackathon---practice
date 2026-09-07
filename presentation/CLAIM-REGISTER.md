# VIGIL claim register — judge-facing use only

Updated: 7 September 2026

This is the source of truth for the rehearsal deck and stage script. A claim not listed as **safe** must not be presented as a result.

## Safe, directly demonstrated

| Claim | Evidence |
|---|---|
| The rehearsal used Elastic/Kibana 9.6.0. | Live deployment version check. |
| 136 seeded, synthetic events were ingested and normalized with the `vigil-normalize` pipeline. | Fresh live validation. |
| Three final behaviour-based alerts and three EQL building-block alerts were generated. | Detection API validation; building blocks are excluded from the final-alert count. |
| Attack Discovery produced one potential discovery from three final alerts. | Private rehearsal execution evidence retained locally; identifiers are not published. |
| An ES\|QL evidence pivot returned 12 correlated events, ₹11,60,000 of suspicious UPI fixture value, and five affected accounts. | Saved VIGIL dashboard and live query. These are scenario facts, not loss estimates. |
| The AI narrative contained five unsupported-certainty phrases and was held for review. | Deterministic guardrail output from `workflow/review_discovery.py`. |
| A full workflow created a case, attached three alerts, invoked an Elastic Agent Builder agent, paused for human input, resumed with `hold`, and completed. | Private rehearsal execution and case evidence retained locally; identifiers are not published. |
| The local evidence ledger contains seven linked blocks; verification passes on the genuine ledger and fails on a tampered copy. | `make demo`. |
| Eleven automated tests pass. | `make test`. |

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
| AWS LLM | Current rehearsal AI used an Elastic preconfigured managed connector. The AWS-LLM path is not yet demonstrated and must be completed during the event before claiming rule compliance. |

## Remove from all judge-facing material

- 45 minutes to 4.2 minutes, 90% faster, 95% reduction, 60% false-positive reduction.
- 50,000+ alerts per day, four hours of paperwork, or any other unsourced industry-volume figure.
- 100% audit-proof, zero hallucination, zero breaches, or guaranteed compliance.
- A ₹5 lakh RBI reporting threshold, “RBI Section 4.2,” or a ₹1 crore penalty avoided.
- “Official CERT-In Annexure-1 PDF.” Annexure I is the incident-type list; the separate Incident Reporting Form is non-mandatory guidance.
- S3 Object Lock, KMS signing, AWS Bedrock, Sarvam translation, multilingual support, or production data localization as features already demonstrated.
- STIX/TAXII as the CERT-In incident-report submission format. STIX/TAXII may be useful for threat-intelligence exchange, but it is not the public incident-reporting form contract.
