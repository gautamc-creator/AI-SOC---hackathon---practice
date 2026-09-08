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
2. **Classify and gather:** deterministic code creates a preliminary classification and SHA-256 evidence envelope; it makes no LLM or production-model claim.
3. **Detect and investigate:** two threshold rules and one EQL sequence rule create three behavior-based final alerts; Elastic Attack Discovery generates a *potential* investigation lead.
4. **Ground the impact:** ES|QL `LOOKUP JOIN` connects the host to synthetic bank context and calculates exposure deterministically.
5. **Decide:** the analyst records `approve`, `hold`, or `reject`; this demonstration records intent only and never contains a system.
6. **Prepare:** VIGIL produces human-review-only RBI DAKSH, CERT-In, optional STIX 2.1 and notification-preview artifacts. Nothing is sent.
7. **Challenge the AI:** a deterministic claim-safety check flags certainty or attribution that the evidence does not establish. It is a phrase-level guardrail, not a second incident verdict.
8. **Prove and present:** a live Elastic Security case holds the three component alerts; a SHA-256 evidence ledger is independently verified and the Golden Path proves tampering is detected. Run `make warroom`, then `python3 -m http.server 8000` at repository root and open `http://localhost:8000/warroom/`.

## SOC cockpit (War Room)

`make demo && make serve` then open `http://localhost:8000/warroom/`. The cockpit reads only
generated artifacts from `warroom/data/` — nothing on screen is assembled by the page or typed
into the markup. It carries:

- a six-step investigation stepper with auto-run and step-through;
- the accountability gate front and centre: what Attack Discovery asserted next to the
  certainty VIGIL refused to treat as established;
- the evidence timeline, exposure cross-check, human decision gate and compliance pack;
- attack topology and a MITRE ATT&CK matrix, both derived from sealed evidence event ids
  rather than drawn by hand;
- **client-side ledger verification.** The page recomputes every block digest from its
  canonical bytes with Web Crypto instead of trusting the stored hash, runs a visible
  canonicaliser self-test, and offers an "Alter one evidence value" control that breaks the
  chain live. Its algorithm reproduces all seven stored digests including the non-ASCII blocks;
- the Bedrock brief with its grounding verification, the Sarvam regional brief with its
  rupee-magnitude re-check, the CERT-In draft with print-to-PDF export, escalation payloads,
  and a provenance tab answering "how do you know that?" for every surface.

`make site` stages the whole thing as static files (~103 KB, no server, no cold start) and
refuses to publish if any staged file contains a value from `.env` or an AWS/PEM/endpoint
credential shape. Deploy free with `make deploy-vercel`, or push to `main` and let
`.github/workflows/pages.yml` regenerate the artifacts, run the tests and publish to Pages.

## Sponsor integrations

Both are implemented and dependency-free, and both write an explicit `NOT_RUN` artifact without a
credential. Each is claimable only when its artifact says `CAPTURED` — see
[claim register](presentation/CLAIM-REGISTER.md).

- **AWS Bedrock** (`make bedrock-probe`, `make brief-live`). Standard-library SigV4, Amazon Nova
  through the Converse API, and model/profile auto-discovery. In Mumbai the client prefers the
  `apac.amazon.nova-micro-v1:0` cross-region inference profile; Anthropic is deliberately not a
  dependency. Output is capped
  at 600 tokens and temperature 0, and the artifact records the real model id, token counts,
  measured latency and an estimated cost. `make brief-adversarial` runs a deliberately loose
  prompt to prove the grounding verifier fires rather than always passing.
- **Sarvam AI** (`make localise`). A live capture on 8 September translated this run's brief into
  Hindi, Marathi, Tamil, Telugu and Bengali, then re-checked that the incident's rupee
  magnitude survived localisation — in Latin or Indic digits — because a
  regional brief that misstates the exposure is worse than no regional brief. There is no
  pre-written regional text anywhere in the repository.

The grounding verifier is the point of the AI layer: the prompt is built from a closed fact set
derived only from the sealed evidence ids, and every number at or above 1,000, every IPv4
literal and every UPI transaction id in the generated text is matched back against that fact
set. Indian scale words are resolved first, so `11.6 lakh` verifies as the same claim as
`1,160,000` while `3.5 crore` is rejected. Anything ungrounded is blocked from every compliance
artifact.

The live rehearsal deployment also contains a supported Elastic 9.6 typed dashboard with three ES|QL evidence metrics and a timeline. `make dashboard-live` upserts it and verifies all five panels by reading the dashboard back. `make workflow-agent-test` proves the controlled Agent Builder evidence-gap step; `make workflow-human-gate-test` proves the native three-way decision gate. `make workflow-e2e-test` is an explicitly live, synthetic test: it creates one case, attaches three alerts, runs the constrained agent, pauses for `approve` / `hold` / `reject`, records `hold`, and verifies the case. It has no containment, external notification, or submission step.

Read [data provenance](data/DATA-PROVENANCE.md) and the [field/schema decisions](data/SCHEMA.md) before presenting the corpus. They make the synthetic-data boundary, source, event fields, and live ingest proof explicit.

For the defensible, source-backed answer to “does this look like the real world?”, see the [realism and format audit](docs/REALISM-AND-FORMAT-AUDIT.md). It states exactly which formats are aligned, which are drafts, and which claims are prohibited.

For the evidence mapped to the judging rubric and the remaining build order, see the [judge-readiness audit](docs/JUDGE-READINESS.md).

## Comparison, provenance, and adversarial testing

- `make eval-compare` runs eight labelled synthetic scenarios (`eval/scenarios.py`: 3 malicious, 3 benign-suspicious,
  1 incomplete-evidence, 1 prompt-injection) through Elastic-rules-alone, Attack-Discovery-alone, and
  Attack-Discovery+VIGIL, and writes `artifacts/eval/COMPARISON-RESULTS.md`. It never fabricates AI-narrative
  metrics for scenarios that have no real captured Attack Discovery run — see [docs/EVAL-LIVE-CAPTURE.md](docs/EVAL-LIVE-CAPTURE.md)
  to fill those in for real, in an isolated index, without touching the frozen demo corpus.
- `make field-provenance` classifies every field in the regulatory drafts as observed, calculated, hardcoded,
  analyst-required, not-observed, or LLM-generated, and cross-checks that the two independently-meaningful
  exposure figures actually agree. Writes `artifacts/FIELD-PROVENANCE-AUDIT.md`.
- `make test-adversarial` covers prompt injection in logs, fabricated amounts in generated prose, missing/duplicated
  events, malformed timestamps, cross-incident evidence contamination, and ledger reordering/deletion/forgery. See
  [docs/ADVERSARIAL-TEST-PLAN.md](docs/ADVERSARIAL-TEST-PLAN.md) for the one item that needs a live environment
  instead of a local test.
- `make scan-injection` runs a standalone deterministic scan for prompt-injection markers in raw event messages,
  independent of any classification/exposure decision.
- Detection coverage is seven candidate rules, none of which pins a host, address, user or account literal —
  asserted by `test_rule_queries_contain_no_hardcoded_indicator`. Rule 04 thresholds on
  `vigil.bank.aml_risk_score >= 85` and rule 05 alerts on a UPI transfer to a beneficiary
  without completed KYC. Rules 06 and 07 close the evaluation harness's insider KYC-tampering
  and duplicate-settlement coverage gaps; they remain disabled until replayed against an isolated
  live evaluation index. The AML score separates the hero (88.7–94.5) from benign settlement
  traffic (0.5–8.0) with no overlap. The deterministic exposure calculation now de-duplicates
  repeated transaction ids, so the duplicate-settlement fixture reports ₹8,30,000 rather than
  double-counting ₹16,60,000.

The ES|QL exposure query is a template, rendered by `make exposure-query` from the host, principal
user and time range in the sealed evidence envelope. The rendered query is published as an artifact
and shown verbatim in the cockpit; the template contains no fixed fixture identity or address.

## Presentation and rehearsal pack

- [Verified rehearsal pitch](presentation/VIGIL-Verified-Rehearsal-Pitch.pptx) — nine judge-facing slides with speaker notes and primary-source links.
- [Claim register](presentation/CLAIM-REGISTER.md) — the only approved source for stage claims.
- [Stage script](presentation/STAGE-SCRIPT.md) — 90-second and three-minute versions.
- [Demo cue sheet](presentation/DEMO-CUE-SHEET.md) — primary path, recovery branches, and pre-stage checks.
- [Judge Q&A](presentation/JUDGE-QA.md) — direct answers to the expected technical, data, compliance, and originality questions.
- [Event-day rebuild](presentation/EVENT-DAY-REBUILD.md) — the clean-room implementation order and evidence log requirements.

The original submission PDF and earlier pitch deck describe the idea that was submitted, but they do not describe the current rehearsal accurately. Do not present them without the corrections in the claim register.

## Live Elastic gate

After the local run passes, follow [docs/ELASTIC-CHECKLIST.md](docs/ELASTIC-CHECKLIST.md). The live demonstration is not complete until it shows:

1. the synthetic data in Elasticsearch;
2. a real alert and Attack Discovery output using the configured LLM connection, labelled accurately as Bedrock-backed only after Bedrock is actually configured;
3. the saved ES|QL lookup join; and
4. the local human-review draft and passing/failing ledger verification.

Run `make benchmark` only for the local deterministic path. Its output explicitly excludes Elastic/LLM/network latency and must not be presented as a production SLO.

`make workflow-live` validates and saves the human-gated Elastic workflow **disabled**. The complete sequence is proven through a controlled manual test harness, but automatic Attack Discovery alert-trigger attachment is not. Keep the saved trigger disabled until that event binding is tested in the event environment; do not describe the system as autonomously responding.

## Key limitations

- Synthetic data only; the rupee amount is deterministic fixture context, not a production risk calculation.
- Attack Discovery produces a potential discovery, not a guaranteed validated incident.
- The CERT-In-compatible / RBI DAKSH artifact is a draft for human review. VIGIL never files with a regulator.
- The local ledger is SHA-256 hash chained. S3 Object Lock and KMS signing are intentional future enhancements.
- The STIX JSON is an interoperability draft, not a statement that a recipient currently requires or accepts it.
