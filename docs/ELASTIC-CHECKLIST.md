# Live Elastic gate

Use this only after the local golden path passes. Record screenshots or exports in the demo folder; do not claim a live feature merely because this checklist exists.

1. Create an Elastic Security project with a tier that includes Attack Discovery and workflows.
2. Configure the approved Amazon Bedrock-backed LLM connection. Prefer **AI Connector → Amazon Bedrock** if it is present in the current UI; the legacy Amazon Bedrock connector is being deprecated. Confirm the model, connection identifier, region, and successful test in the live UI.
3. Run `cp .env.example .env`, add the Elasticsearch endpoint, Kibana endpoint, and API key locally, then run `make seed`. The script creates **only** `logs-vigil-security` and `vigil-bank-context`; it deletes/recreates those two synthetic demo data stores on each run.
4. Open and run `elastic/esql/exposure_lookup_join.esql` in ES|QL. Save it and add it to the Kibana demo dashboard.
5. Run `make create-rule`. The checked-in custom query rule intentionally creates twelve related alerts from the injected hero evidence, so Attack Discovery has an honest alert-correlation job. It is a demo rule, not a claim that this is a production detection strategy.
6. Run Attack Discovery against the resulting alert(s) using the tested Bedrock-backed LLM connection. Preserve the actual discovery output.
7. Capture the real discovery alongside the local report draft. If the Attack Discovery result does not establish the expected relationship, describe it truthfully as an investigation lead, not a confirmed incident.

Do not automate a regulator portal. The VIGIL report is explicitly a human-review draft.
