# VIGIL judge-readiness audit

Reviewed: 7 September 2026. This is an evidence-based rehearsal assessment, not a promise of placement.

## Bottom line

VIGIL is now a credible, focused prototype: Elastic detects and correlates suspicious behavior; VIGIL grounds the AI lead in bank context, catches unsupported certainty, requires a human decision, and prepares review-only evidence/reporting artifacts. The strongest differentiator is not “another SOC copilot”; it is the accountable bridge from an AI investigation lead to a defensible bank decision.

The prototype is competitive but not presentation-complete. The native Kibana evidence dashboard and a controlled full workflow—case, three alerts, Agent Builder review, resumable human gate and decision record—are proven. The remaining high-value work is event-environment trigger binding, sponsor-model integration, permitted backup evidence, and repeated stage rehearsal. Do not add a second scenario until this path is visually flawless.

## Evidence already proven

| Proof | Observed rehearsal result | Claim boundary |
|---|---|---|
| Ingest | 136/136 synthetic ECS-aligned events enriched by `vigil-normalize`. | Pipeline behavior, not production throughput. |
| Detection | Two threshold rules and one EQL sequence rule succeeded. Exactly three final alerts; three EQL building blocks are excluded from Attack Discovery. | Behavior-based fixture conformance, not measured detection accuracy. |
| Correlation | Direct EQL returned exactly one login → egress → payment sequence. | One deterministic scenario. |
| Retrieval | ES|QL host/user/time-window pivot + `LOOKUP JOIN` returned 12 events, INR 1,160,000 fixture exposure and five affected accounts. | Fixture exposure, not proven loss. |
| AI investigation | One fresh Attack Discovery run correlated all three final alerts into one potential discovery. | Elastic preconfigured-LLM baseline; not AWS Bedrock. |
| AI governance | Deterministic review flagged five certainty/attribution phrases such as “confirmed” and “fraudulent.” | Phrase-level guardrail, not semantic fact checking. |
| Case management | One live Elastic Security case was created with all three component alerts attached. | Synthetic rehearsal case only. |
| Elastic dashboard | A supported Elastic 9.6 typed dashboard rendered three correct ES\|QL metrics (12 evidence events, INR 1,160,000 fixture total, five accounts) and the incident timeline. | Fixed synthetic scenario, not a production dashboard or loss calculation. |
| Elastic Workflow | The saved alert-triggered definition validates and remains disabled. A controlled manual full-chain test completed all eight steps in 70,927 ms: case, three alert attachments, Agent Builder review, pause, `hold`, and decision comment. | Full manual rehearsal path is proven; automatic alert-trigger event binding is not. Preconfigured Elastic Claude 5 used 21,852 tokens. |
| Human control | `approve` / `hold` / `reject` record; demo uses `hold`. | No containment is executed. |
| Evidence integrity | Seven-block SHA-256 chain passes; a one-value modification fails. | Tamper-evident prototype, not immutable storage or digital signature. |
| Local performance | Five-run median for deterministic local path is recorded in `benchmarks/local-rehearsal.json`. | Excludes Elastic, LLM, browser and regulator systems; not an SLO. |

## Rubric alignment

| Judge area | What to show | Current status | Highest-value improvement |
|---|---|---|---|
| Innovation / AI | Attack Discovery creates a lead; VIGIL visibly detects AI overclaim and grounds impact before human action. | Strong and differentiated. | Put “AI said confirmed; VIGIL refused to treat it as confirmed” at the center of the story. |
| Technical / Elastic | Data stream, ingest pipeline, threshold + EQL rules, Attack Discovery, ES|QL lookup, typed dashboard, Security Case, Agent Builder and native human gate. | Strong live backend, UI and controlled workflow proof. | Test automatic alert-trigger binding in the event environment. |
| Impact | Five-account, INR 11.6 lakh synthetic exposure plus review-ready incident information under time pressure. | Clear, but scenario-specific. | Show time saved as workflow steps removed, not an invented percentage. |
| UX | Offline War Room gives one decision surface and survives network failure. | Functional. | Polish the War Room and use Kibana as the evidence drill-down, not a competing UI. |
| Presentation | Three-minute runbook and honest claim boundaries exist. | Not yet rehearsed. | Three timed rehearsals, judge Q&A, and a permitted backup recording. |

## Real-world fit and limits

- Events use ECS categories/types, standard host/user/source/destination/HTTP/transaction fields, and namespaced bank-specific context.
- The payment API event is intentionally not presented as an NPCI/UPI wire message. A production version would map bank gateway, IAM, WAF, application and payment-switch telemetry into ECS through source-specific integrations.
- The benign maintenance decoy tests that internal failed logins below threshold do not become this incident chain.
- The CERT-In draft mirrors public information groups; reporter/entity fields stay blank until an authorised person supplies them.
- RBI output is an information pack. Applicable entity type and current submission workflow must be confirmed by the bank's compliance owner.
- Attack Discovery language is stored as generated evidence, but VIGIL does not silently adopt its conclusions.

## Build next, in order

1. Test the saved workflow's automatic Attack Discovery alert-trigger binding in the event environment. The same eight-step sequence is already proven through the controlled manual harness. Do **not** auto-isolate a synthetic host merely for spectacle.
2. Add an event-day sponsor model only after a real successful connector test; label the present preconfigured Elastic baseline accurately until then.
3. Rehearse normal, slow-network and offline flows. Capture screenshots and a backup only if rules allow it.
4. Freeze the core. Spend remaining time on narrative, visual hierarchy and Q&A—not new features.

## Features deliberately deferred

- Real regulator submission, automated containment, S3 Object Lock/KMS, production fraud scoring, a real UPI feed, Slack paging, multi-tenant authorization, and a second attack scenario.
- These are credible production extensions, but weak hackathon additions unless they can be proven safely and live.

## Stage-safe headline

“Elastic found a potential attack. VIGIL showed what the bank could lose, caught the AI overstating certainty, preserved the evidence, and required an accountable human decision before any action or report.”
