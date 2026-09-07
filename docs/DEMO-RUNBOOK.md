# VIGIL rehearsal demo runbook

## Before presenting

```bash
make demo
make test
python3 -m http.server 8000
```

Open `http://localhost:8000/warroom/`. For the live Elastic segment, first run the checklist in `ELASTIC-CHECKLIST.md` and keep Kibana open at the prepared view.

## Three-minute narrative

1. **Problem (20 sec):** Elastic can correlate alerts, but a bank analyst still has to determine exposure, take an accountable decision, and assemble reviewable reporting evidence under time pressure.
2. **Detection (30 sec):** Show the synthetic payment-service sequence in Kibana and the alert rule. State that the data is synthetic.
3. **AI lead and guardrail (40 sec):** Show Attack Discovery, then the VIGIL claim-safety warning. Say: “The model connected the evidence, but it also said ‘confirmed’ and ‘fraudulent.’ VIGIL refuses to turn that language into an autonomous decision.” State the actual configured LLM path.
4. **Grounded impact (35 sec):** Show the ES|QL host/user/time-window pivot and `LOOKUP JOIN`: it turns the alert context into five affected accounts and ₹1,160,000 fixture exposure without querying the hidden hero tag.
5. **Human accountability (30 sec):** In the War Room, show the `hold` decision. Emphasize that VIGIL does not automatically contain systems or submit reports.
6. **Case, evidence and reporting (25 sec):** Show the Elastic Security case with three attached alerts, review-only DAKSH/CERT-In/STIX drafts, then the hash chain passing and the altered copy failing.
7. **Close (10 sec):** “VIGIL turns a potential discovery into a defensible, human-owned bank decision—not an autonomous compliance claim.”

## Do not say

- “VIGIL filed with RBI or CERT-In.”
- “Attack Discovery confirmed the breach.”
- “This baseline uses AWS Bedrock” unless the live configuration proves it.
- Any unmeasured accuracy, savings, latency, or regulatory claim.
