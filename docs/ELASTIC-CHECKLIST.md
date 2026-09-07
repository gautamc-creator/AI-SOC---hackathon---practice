# Live Elastic gate

Use this only after the local golden path passes. Record screenshots or exports in the demo folder; do not claim a live feature merely because this checklist exists.

1. Create an Elastic Security project with a tier that includes Attack Discovery and workflows.
2. Configure the approved Amazon Bedrock-backed LLM connection only when access is available. Until a real test succeeds, use and label the present preconfigured Elastic connector as a non-Bedrock baseline.
3. Run `cp .env.example .env`, add the Elasticsearch endpoint, Kibana endpoint, and API key locally, then run `make seed`. The script creates **only** `logs-vigil-security` and `vigil-bank-context`; it deletes/recreates those two synthetic demo data stores on each run.
4. Open and run `elastic/esql/exposure_lookup_join.esql` in ES|QL, then run `make dashboard-live`. The script upserts `vigil-evidence-dashboard` through the supported typed Dashboards API and reads it back. Confirm visually that it shows 12 evidence events, INR 1,160,000 fixture total, five accounts and the timeline.
5. Run `make create-rule`, `make validate-detection-queries`, `make validate-rules`, and `make validate-alerts`. Expect two threshold rules, one EQL sequence rule, three final alerts and three internal EQL building blocks. The obsolete tag-based rule is disabled automatically.
6. Run Attack Discovery against final alerts only. Preserve the actual output and actual connector label.
7. Capture the discovery, run `make demo`, and show the AI claim-safety finding. If generated language says “confirmed,” “fraudulent,” or attributes an attacker, present that as a VIGIL review flag—not as fact.
8. Run `make case-live` once to create a synthetic Elastic Security case and attach all three component alerts. Do not create repeated duplicate cases during the stage demo.
9. Run `make workflow-live` to validate and save the workflow disabled. `make workflow-e2e-test` is intentionally side-effecting and should be run only once per rehearsal: the verified run completed all eight controlled steps in 70,927 ms, created case `0da84a76-6dd9-419d-b4de-3c1734d67176`, attached three alerts, used 21,852 preconfigured-connector tokens, paused and resumed with `hold`. Enable or attach the automatic alert trigger only after testing its event binding in the target environment.

Do not automate a regulator portal. The VIGIL report is explicitly a human-review draft.
