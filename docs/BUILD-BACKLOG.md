# VIGIL build backlog — 8 to 17 September 2026

Ranked work for the pre-event window, mapped to the published rubric. Written 8 September 2026.

**Read this first:** the judged build starts **18 September**. Nothing here is the submission.
Everything in this repository is a disclosed pre-event spike, and the organisers expect that —
"test things out before you arrive, try approaches, spike ideas, learn the tooling." The purpose
of this backlog is to make the 18th an *execution* day, not a discovery day. Every item below
should end with a rehearsed, repeatable procedure recorded in
[EVENT-DAY-REBUILD.md](../presentation/EVENT-DAY-REBUILD.md).

## Lane ownership — two agents are working this repo concurrently

| Lane | Owner | Scope | Status |
|---|---|---|---|
| **A** | Agent already in flight | AWS Bedrock, Sarvam, **public deploy, wiring the existing mockups, richer bank context fields, escalation dispatchers, PDF export of the draft.** | **In progress.** Scope widened 8 Sep after a competitive review. Do not touch. |
| **B** | Second agent | **Real regulatory corpus and grounded retrieval (T2.1), detection coverage (T2.3).** Everything else moved to Lane A. | In progress. |
| **C** | Whoever lands last | Shared-hot files. Sequence these, never edit concurrently. | Blocked until A and B settle. |

**Re-cut on 8 September.** A competitive review recommended Lane A also take deployment, UI
wiring, scenario breadth, dispatchers and PDF export. That is the right call - those are cheap,
certain points - but it means **T1.3 (cockpit), T2.4 (headline number) and T2.5 (de-hardcoded
retrieval) moved from Lane B to Lane A**, because they all land in files Lane A now owns
(`warroom/*`, `report/generate.py`, the ES|QL). Lane B keeps only work in new directories.

**One correction to that review before Lane A acts on it.** The recommendation to adopt a
top-level `bank.*` field namespace (`bank.aml_risk_score`, `bank.customer_tier`,
`bank.kyc_verified`, `bank.upi_vpa`) should be taken as *field content*, not as *field naming*.
`bank.*` is **not** ECS. ECS reserves the top-level namespace, and custom fields belong under a
vendor prefix precisely so a future ECS release cannot collide with them - which is why this
repository already uses `vigil.bank.*`. Adopting bare `bank.*` would be a step backwards in
schema practice in front of a judge who runs field engineering at Elastic. **Take the richer
fields, keep them under `vigil.bank.*`.** Doing so also closes the "KYC and AML data" row in the
drift table below, which is currently an open promise from our own submission.

**Lane C shared-hot files — collision zone.** Both lanes will want to add targets and prose to
these. Do not edit them from two lanes at once; batch the edits at the end of each lane instead:

- `Makefile` (already dirty)
- `README.md` (already dirty)
- `docs/JUDGE-READINESS.md` (already dirty)
- `.env.example`
- `presentation/CLAIM-REGISTER.md`
- `report/generate.py` and `compliance/generate.py` — Lane A may wire translation in here

**Housekeeping, do first.** The working tree has carried uncommitted work since 7 September
(`field_provenance.py`, `eval/`, `test_adversarial.py`, `scan_for_injection.py`, plus four
modified files) and now has a second agent writing into it. Commit the 7 September state as a
checkpoint before either lane goes further, so the two lanes stay separable and either can be
reverted independently. Consider a branch per lane.

---

## Tier 1 — cannot take first prize without these

### T1.1 · AWS in the actual product path — *Lane A, in flight*

AWS LLM is a **core required technology** and one of the four judges is an AWS Senior Solutions
Architect. There is currently no AWS anywhere in the build; Attack Discovery runs on Elastic's
preconfigured `Anthropic-Claude-Sonnet-3-7` managed connector, correctly labelled as not a
Bedrock demonstration.

- [ ] Bedrock reachable from this repo with a recorded, real model id — never a pinned guess
- [ ] An Elastic **Bedrock connector** driving Attack Discovery, replacing the managed baseline
- [ ] A VIGIL-owned Bedrock call for its own reasoning step, structured JSON, schema-validated
- [ ] Update the `not an AWS Bedrock demonstration` label in `run_attack_discovery.py`,
      `capture_attack_discovery.py`, `field_provenance.py` and both `warroom/data/*.json`
      **only once a real invocation is recorded**

*Scores:* Technology Stack 15, AI Implementation 15.
*Blocker on record:* a live 8 September probe confirmed the non-Anthropic
`apac.amazon.nova-micro-v1:0` profile is valid, but AWS returned “account is currently being
verified.” Invocation must be retried after verification; the IAM identity also lacks optional
`bedrock:ListInferenceProfiles` and `bedrock:ListFoundationModels` discovery permissions.
*Acceptance:* `make bedrock-test` prints a real model id, real token counts, and writes proof to
`artifacts/`. The claim register moves Bedrock from prohibited to permitted.

### T1.2 · Corpus scale — *Lane B*

The submitted problem statement opens with "tens of thousands of alerts every day" and promises
"~30 days of Indian retail-bank telemetry". The corpus is **136 events**. The Elastic judge runs
field engineering at a data platform company and will notice a 136-document demo.

- [ ] Scale `data/generator/generate.py` to a realistic volume with the hero chain buried inside
- [ ] Keep the seed deterministic and the ground-truth answer key exact
- [ ] Re-verify the three rules still fire on exactly the intended events at volume
- [ ] Record real ingest throughput and query latency at the new volume

*Scores:* Elasticsearch Integration 15, Problem Solving 10. Closes a live drift against our own
submission text.
*Acceptance:* the hero chain is genuinely a needle in a haystack, and the ES|QL pivot still
returns the same 12 evidence events.

### T1.3 · A real cockpit — *Lane B*

`warroom/index.html` is one 8-line static file reading JSON off disk. The polished 45KB and 73KB
mockups sit unwired in the parent directory. This is the largest block of near-unclaimed points
in the rubric and the lowest-risk work on this list.

- [ ] Wire the existing design language to live Elastic and the VIGIL outputs, not static JSON
- [ ] Two regulatory clocks, evidence drawer with source event ids, the exact ES|QL on screen
- [ ] Keep the offline fallback path — it is real demo resilience, not a second architecture
- [ ] Kibana stays the evidence drill-down, not a competing UI

*Scores:* Interface Design 8, Usability 7, Demo Quality 5.

---

## Tier 2 — where first prize is actually won

### T2.1 · Ingest the real rulebook, ground the decision in it — *Lane B*

The judges said, verbatim: *"Better still, build a scraper and pull live data. Real, messy,
moving data is harder and the effort shows."* Everything we have is synthetic. We cannot get real
bank telemetry — but the **regulation is public, real, messy and citable**.

**Status: working end to end as of 8 September.** `artifacts/regulatory-grounding-proof.json`.

- [x] Scraper with recorded fetch timestamps, source URLs, SHA-256 and a permission note —
      `regulatory/fetch_sources.py`, 6 real sources, `regulatory/SOURCES.json`
- [x] `semantic_text` availability verified on our project — `.elser-2-elasticsearch` is present,
      along with four rerankers, on Elastic Serverless 9.6.0
- [x] Paragraph-level extraction — `regulatory/extract.py`, 311 citable units, the RBI instrument
      addressable at all 232 of its numbered paragraphs. PDF text recovered with stdlib only
- [x] Indexed with ELSER — `regulatory/index_corpus.py`, 311/311 in 119s into
      `vigil-regulatory-corpus` (a separate index; the script refuses any name outside that prefix)
- [x] Semantic retrieval proven — `regulatory/query.py`. *"How quickly must a bank tell the
      regulator after it spots a break-in?"* returns RBI paragraph 182 as top hit at 10.15 with
      **no keyword overlap**
- [x] **Both clocks now verified against retrieved primary text, not an LLM's memory.**
      RBI para 182 (six hours from *detection*, DAKSH, plus proactive CERT-In notification) and
      the CERT-In Directions clause (6 hours from *noticing*)
- [ ] Apply a reranker — the corpus is RBI-weighted (233 of 311 units) so RBI outranks CERT-In on
      questions where CERT-In is the better authority. `.jina-reranker-v3` is available
- [ ] Generate a cited answer from the retrieved text — right now we retrieve and cite but do not
      generate. **Pair this with Lane A's Bedrock call**: retrieval is Lane B, generation is Lane A
- [ ] Replace the hardcoded regulatory constants in the drafts with retrieved citations
- [ ] An Agent Builder agent with a search tool over this index — the "user question to grounded
      answer" path the judges asked to see
- [ ] Add `make regulatory-*` targets — **deferred, `Makefile` is Lane C**

*Scores:* Originality 10, AI Implementation 15, Elasticsearch Integration 15 (semantic and hybrid
retrieval was **zero** in this repo before this), Problem Solving 10.

**Findings worth putting on a slide.** The RBI page returned different bytes on two fetches minutes
apart (205,016b then 206,573b) — the data really is live and moving, and change detection must hash
normalised text rather than raw bytes. Extraction also initially pulled embedded font programs in
as text; the filter that fixes it is in `_looks_like_prose`, and the bug is worth mentioning as
evidence the corpus was actually inspected rather than assumed.

### T2.2 · Sarvam in the demo — *Lane A, in flight*

One of the four judges is Sarvam's Head of Strategy and GTM for Model APIs. The claim register
currently **prohibits** mentioning Sarvam, so that judge has nothing to score.

- [x] Live Sarvam `/translate` capture over the deterministic incident draft
- [x] Hindi, Marathi, Tamil, Telugu and Bengali captured; ₹ magnitude preserved in all five
- [x] Never use Sarvam to establish a fact — the English draft remains authoritative

*Scores:* Technology Stack 15, Originality 10.

### T2.3 · Close the gaps our own harness found — *implemented locally; live replay pending*

`make eval-compare` honestly reports VIGIL wrong on 2 of 8 scenarios. Both are upstream detection
coverage gaps, not grounding errors. Fixing them converts a disclosed weakness into a strong Q&A
moment: "our harness found it, we closed it."

- [x] Detection rule and faithful local mirror for insider KYC tampering (`m2`)
- [x] Detection rule and faithful local mirror for payment-switch duplicate settlement (`m3`)
- [x] Dedupe by transaction id in the exposure formula — `m3` now computes ₹8,30,000
- [x] Re-run `make eval-compare`; VIGIL is correct on all eight labelled local scenarios
- [ ] Replay rules 06 and 07 in the isolated live evaluation index before calling them live-proven

### T2.4 · Make the headline number actually calculated — *complete*

`deterministic_exposure_inr` — the ₹11,60,000 a judge sees first — is now summed from
the structured transaction amounts in the sealed evidence set. The value in
`ground-truth.json` is retained only as a fail-closed test oracle: report generation stops
if the evidence-derived figure disagrees. The separately displayed observed total agrees.

- [x] Make the headline field the computed one; keep the answer key as a fail-closed assertion only
- [x] Update `compliance/field_provenance.py` with the evidence-derived source

*Why urgent:* one question — "so it isn't calculated, it's looked up?" — currently lands. The fix
is roughly one line and removes the sharpest attack on the whole demo.

### T2.5 · De-hardcode the retrieval — *template path complete; second live scenario pending*

`elastic/esql/exposure_lookup_join.esql` is pinned to a literal host, user and 15-minute window,
so it cannot survive "now run it on a different incident."

- [x] Parameterise host, user and time window from the sealed evidence envelope
- [ ] Prove it on a second scenario from `eval/scenarios.py`

---

## Tier 3 — cheap, do if the lanes clear

- [ ] **Wider platform.** A real Elastic webhook or email connector action delivering the approved
      pack to our own inbox. The judges explicitly asked to see webhooks, email actions and
      integrations. `notifications/prepare.py` is 21 lines of preview only. Post-approval and
      addressed to ourselves, so the risk is nil.
- [ ] **Market Potential 10.** Currently nothing built. Cite the count of scheduled commercial
      banks, UCBs and NBFCs now under the RBI 2026 Directions — citable, sourced, no invented TAM.
- [ ] **Automatic Attack Discovery trigger.** Get a definitive read using Kibana's own workflow
      execution-history UI. Guessed REST endpoints all 404'd. The eight-step sequence is already
      proven through the manual harness regardless, so this is a nice-to-have.

---

## Do not build

Deferred deliberately, and the reasoning still holds. These are credible production extensions
and weak hackathon additions:

S3 Object Lock, KMS signing, autonomous containment, EKS or VPC or PrivateLink, multi-tenant
authorization, a real UPI or NPCI feed, real regulator submission, production fraud scoring.

**Never**, regardless of time available: autonomous containment of any host, any claim of filing
with a regulator, invented metrics or penalty figures, or real customer data in a prompt.

---

## Drift against our own submission — rehearse answers for these

Judges will have the submission text. These have moved, and the Q&A needs a prepared, confident
answer for each rather than an improvised one.

| Submission promised | Current reality | Action |
|---|---|---|
| "deployed on AWS" | No AWS at all | Close via T1.1 |
| "six steps, **each** invoking an Agent Builder agent" | One `ai.agent` step; rest deterministic Python | Close partly via T2.1; otherwise explain — determinism for money math is the *better* answer |
| "account, customer-tier, **KYC and AML** data" | Lookup index has service, tier, owner, exposure, account_count. No KYC or AML fields | Add the fields or drop the claim |
| "Sarvam Indic-language reports" | Not built, claim prohibited | Close via T2.2 |
| "60% FP reduction, 45min to under 5min" | Removed as unsupported | **Rehearse this.** "We could not source it, so here is what we measured instead" is a strength delivered confidently and a wound if fumbled |
| "~30 days of telemetry" | 136 events | Close via T1.2 |
| "measured against two baselines: rules alone, AD out of the box" | Built exactly as promised | Lead with this — a kept promise is rare |
