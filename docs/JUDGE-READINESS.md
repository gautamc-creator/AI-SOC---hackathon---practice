# VIGIL judge-readiness audit

Reviewed: 7 September 2026 (updated same day with the comparison harness, field-provenance audit, adversarial
tests, and one attempted live automatic-trigger test — see the new section below). This is an evidence-based
rehearsal assessment, not a promise of placement.

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
| Indic localisation | Live Sarvam capture produced Hindi, Marathi, Tamil, Telugu and Bengali briefs; ₹11,60,000 survived all five magnitude checks. | Internal readability aid; English remains authoritative and Sarvam establishes no facts. |
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

## New since the last audit: comparison harness, field provenance, adversarial tests

- **Comparative evaluation** (`make eval-compare`): eight labelled scenarios (3 malicious, 3 benign-suspicious, 1
  incomplete-evidence, 1 prompt-injection) run through rules-alone, Attack-Discovery-alone, and Attack-Discovery+VIGIL.
  Current local results: naive rules-alone escalation is wrong on 3/8 scenarios because a binary baseline cannot
  express a hold or bank-context exception; VIGIL's grounded decision layer is correct on 8/8. Candidate rules 06 and
  07 close the insider KYC-tampering and duplicate-settlement gaps in the local predicate mirror, and transaction-id
  de-duplication now computes the duplicate-settlement fixture correctly. The two new Elastic rule definitions remain
  disabled until replayed in an isolated live evaluation index; do not call them live-proven. See
  `artifacts/eval/COMPARISON-RESULTS.md`. The AI-narrative-dependent cells are real only for the hero scenario;
  the other seven are explicitly `NOT_YET_CAPTURED`, not fabricated — see `docs/EVAL-LIVE-CAPTURE.md` to fill
  them in live, in an isolated index, without touching the demo path.
- **Field-provenance audit** (`make field-provenance`): every field in the incident/CERT-In/RBI drafts is classified
  as observed, calculated, hardcoded, analyst-required, not-observed, or LLM-generated, with a live cross-check that
  the two independently-meaningful exposure figures (`deterministic_exposure_inr` vs
  `observed_suspicious_upi_total_inr`) actually agree. Found 8 hardcoded-constant fields that will not generalize
  past the hero scenario (e.g. `incident_type`, `mission_critical_system.value`, several IP/host fields copied as
  literals instead of read from evidence). See `artifacts/FIELD-PROVENANCE-AUDIT.md`.
- **Adversarial tests** (`make test-adversarial`): prompt injection in log messages, fabricated amounts in generated
  prose, missing/duplicated events, malformed timestamps, cross-incident evidence contamination, and ledger
  reordering/deletion/forgery are all covered and passing. Unauthorized workflow resumption is documented as a
  live-environment procedure (not fakeable locally) in `docs/ADVERSARIAL-TEST-PLAN.md`.
- **Automatic Attack Discovery trigger — attempted, inconclusive.** Enabled the saved workflow live (confirmed via
  the API, not assumed), generated a fresh Attack Discovery execution, and polled for an auto-created case for 60
  seconds: none appeared. Reverted to disabled and confirmed via the API. Also found and fixed a real bug:
  `elastic/create_workflow.py` was hardcoding `"enabled": false` in its own proof output regardless of what was
  actually saved, so this exact claim was never actually being verified before. Full procedure and result in
  `artifacts/workflow-auto-trigger-test.json`. This still needs dedicated time with Kibana's own workflow
  run-history UI at the event — guessed REST endpoints for execution history all 404'd in this session.

## Build next, in order

1. Get a definitive read on the automatic Attack Discovery alert-trigger binding using Kibana's own workflow
   execution-history UI (not guessed REST endpoints) — see `artifacts/workflow-auto-trigger-test.json` for what
   was already tried. The eight-step sequence is already proven through the controlled manual harness regardless.
   Do **not** auto-isolate a synthetic host merely for spectacle.
2. Add an event-day sponsor model only after a real successful AWS Bedrock connector test; label the present
   preconfigured Elastic baseline accurately until then. Use `docs/EVAL-LIVE-CAPTURE.md`'s per-scenario procedure
   to capture real (not simulated) Attack-Discovery narrative metrics once that connector exists.
3. Rehearse normal, slow-network and offline flows. Capture screenshots and a backup only if rules allow it.
4. Freeze the core. Spend remaining time on narrative, visual hierarchy and Q&A—not new features.

## Features deliberately deferred

- Real regulator submission, automated containment, S3 Object Lock/KMS, production fraud scoring, a real UPI feed, Slack paging, multi-tenant authorization, and a second attack scenario.
- These are credible production extensions, but weak hackathon additions unless they can be proven safely and live.

## Stage-safe headline

“Elastic found a potential attack. VIGIL showed what the bank could lose, caught the AI overstating certainty, preserved the evidence, and required an accountable human decision before any action or report.”
