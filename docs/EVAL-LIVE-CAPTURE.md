# Filling in the live Attack Discovery cells

`eval/run_comparison.py` computes real, reproducible metrics for the rules-alone
predicate mirror and the deterministic VIGIL grounding/decision layer across
all eight `eval/scenarios.py` fixtures — no live call is needed for those.

The **Attack-Discovery-alone narrative metrics** (unsupported-claims count,
generation duration, connector/token accounting) are real today only for
`m1_credential_theft_to_bulk_upi`, because that is the one scenario with an
actual captured run in `artifacts/attack-discovery-baseline.json`. The other
seven scenarios are marked `NOT_YET_CAPTURED` rather than filled in with
invented narrative text — this repository does not fabricate LLM output.

Do this **only in an isolated index**, never against `logs-vigil-security`
(the live demo's index) — the demo path must stay visually flawless per
`docs/JUDGE-READINESS.md`.

## Procedure per scenario

1. Pick one scenario from `eval/scenarios.py`, e.g. `m2_insider_kyc_tampering`.
2. Write its `events` list to a throwaway data stream, e.g.
   `logs-vigil-eval-m2` (not `logs-vigil-security`), using the same
   `elastic/ingest/vigil-normalize.json` pipeline and `elastic/mappings/`
   templates so field shapes match what the live rules expect.
3. The deployed detection rules (`elastic/rules/*.json`) hardcode
   `user.name: "svc-payments-admin"` and the `outside_normal_batch` /
   `vigil_hero`-adjacent field names. For scenarios other than m1, b2, i1, and
   p1 (which reuse that principal), you must either:
   - temporarily clone a rule with the scenario's actual principal
     substituted, run it against the isolated index, then delete the clone; or
   - accept that no rule fires (this is itself the finding for m2/m3 — see
     `artifacts/eval/COMPARISON-RESULTS.md`'s "detection-coverage-gap" note)
     and skip straight to a manual Attack Discovery ad-hoc run over the raw
     alerts you create by hand for the test.
4. Run `elastic/run_attack_discovery.py` (or the ad-hoc API) against only the
   isolated index's alerts.
5. Run `elastic/capture_attack_discovery.py <execution_uuid>` to save the
   output — save it as `artifacts/eval/attack-discovery-<scenario_id>.json`,
   NOT over `artifacts/attack-discovery-baseline.json` (that file is the
   hero scenario's proof and must not be overwritten).
6. Feed the captured text through `workflow/review_discovery.py`'s
   `RISKY_CLAIMS` check (or `eval/run_comparison.py::claim_review_text`) to
   get a real unsupported-claims count.
7. Record the connector id, `generation.average_successful_duration_nanoseconds`,
   and any token-usage field the connector response exposes (the current
   Elastic-managed connector capture does not expose a token count — an AWS
   Bedrock connector's response may; check before claiming a token figure).
8. Delete the isolated index and any cloned rule when done.

## Why this matters for the AWS Bedrock proof gap

Every real capture done this way should also record the **connector label**
(`connector_id` / `connector_name`). Per `docs/JUDGE-READINESS.md` and
`HACKATHON_EXECUTION_PLAN.md`, the only capture that exists today
(`Anthropic-Claude-Sonnet-3-7`) is Elastic's preconfigured connector, not an
AWS Bedrock connector. Until a real Bedrock-backed connector test succeeds,
label every comparison row from this procedure the same way: "Elastic
preconfigured-LLM baseline — not an AWS Bedrock demonstration."
