# VIGIL stage script

The exact pitch and Q&A duration is still organizer-confirmation dependent. Rehearse the 90-second version first, then the three-minute version.

## 90-second version

**0:00–0:12 — Hook**

“A bank can detect the right alert and still fail the incident. The hard part is turning uncertain security evidence into an accountable decision and a regulator-ready draft before two six-hour clocks expire.”

**0:12–0:27 — Product position**

“Elastic already gives us detection, Attack Discovery, Cases, Workflows, and Agent Builder. VIGIL does not rebuild them. It adds the bank-specific bridge: raw-evidence grounding, a rupee-valued payment pivot, compliance-field preparation, a human decision gate, and independently checkable evidence.”

**0:27–0:47 — Live dashboard**

“This is seeded synthetic data, clearly labelled. Elastic correlated 12 evidence events. One ES|QL pivot joins the compromised service context to five bank accounts and ₹11.6 lakh of suspicious UPI fixture value. That is scenario value—not proven loss.”

**0:47–1:05 — AI guardrail + gate**

“Attack Discovery gave us a useful lead, but it also used unsupported certainty such as ‘confirmed’ and ‘fraudulent.’ VIGIL flags those phrases, opens a case with the source alerts, and pauses. Here the analyst selected HOLD. Nothing destructive and nothing regulatory was sent.”

**1:05–1:20 — Evidence proof**

“The approved or held decision becomes a seven-block evidence chain. The standalone verifier passes the genuine chain and fails after one record is altered.”

**1:20–1:30 — Close**

“VIGIL turns an AI-generated lead into a bank decision that can be challenged, reviewed, and defended—without pretending uncertainty has disappeared.”

## Three-minute version

Use the 90-second flow, with these additions:

- After the hook, explain the anchors precisely: RBI DAKSH is six hours from detection for banks covered by the 2026 commercial-bank Directions; CERT-In is six hours from noticing for listed incident types.
- At the dashboard, show the actual ES|QL `LOOKUP JOIN` and say why each bank-specific field sits outside ECS.
- At the gate, show the workflow execution status changing from `WAITING_FOR_INPUT` to completed after `hold`.
- At the ledger, run both genuine and tampered verification.
- Close with the event-day disclosure: “We rehearsed this architecture beforehand. The judged implementation is being rebuilt in the official repository from the event start, and we will disclose exactly what was created during the event.”

## Words to use

- potential incident
- synthetic scenario
- suspicious fixture value
- evidence-backed draft
- human-review required
- simulated decision
- tamper-evident / independently verifiable

## Words to avoid

- confirmed attack or fraud
- loss prevented
- official filing
- audit-proof
- zero hallucination
- automatic containment
- guaranteed compliance

