# VIGIL judge Q&A

## What does VIGIL add that Elastic does not already provide?

Elastic supplies the security platform: ingestion, detection, Attack Discovery, ES|QL, Cases, Workflows, Agent Builder, and the dashboard. VIGIL adds the bank-domain contract around those primitives: deterministic payment-context joins, regulator-field mapping, an unsupported-certainty guardrail, a human decision gate, and a standalone evidence-chain verifier.

## How do you know the AI is not hallucinating?

We do not claim that it cannot hallucinate. The rehearsal caught five unsupported-certainty phrases in the generated discovery. Every material number is recomputed from indexed evidence, the source alert IDs are attached to the case, and a human must decide before any downstream action. The system fails closed when evidence is missing.

## Is ₹11.6 lakh the amount stolen?

No. It is the deterministic total of suspicious UPI fixture records linked to the synthetic scenario. It is a prioritization input, not a fraud finding, realized loss, or loss prevented.

## Is the data real?

No. It is seeded synthetic data because production banking telemetry is sensitive and unavailable for a hackathon. The security fields are ECS-aligned; payment/customer context uses an explicit bank namespace and lookup index. It is not represented as NPCI wire-format or production bank data.

## Is STIX/TAXII required for CERT-In reporting?

Not by the public six-hour incident-reporting direction or its published form. The public contract is the listed incident categories and relevant incident information. STIX/TAXII can be an optional threat-intelligence exchange integration, not the filing format.

## Does VIGIL submit directly to RBI or CERT-In?

No. It prepares a human-review draft and DAKSH preparation pack. The prototype never submits to a regulator. Production submission would need bank authorization, portal integration, legal review, segregation of duties, and operational controls.

## Did the prototype contain or freeze anything?

No. The workflow stops at a human `hold` decision. Containment is simulated/logged. No host, account, token, or payment was changed.

## Where is AWS in the demonstrated path?

In the current rehearsal it is not yet in the AI path; the successful run used Elastic’s preconfigured managed connector because Anthropic Bedrock access was unavailable on the personal account. We will only claim rule compliance after the judged build invokes an AWS-hosted LLM and records that model/connector evidence. The rehearsal exists to remove the remaining Elastic and workflow risk before the event.

## Why not use Amazon Nova through the Elastic Bedrock connector?

Elastic’s current Amazon Bedrock connector documentation supports Anthropic Claude models. Amazon Nova is a possible AWS-native model for a separate service or inference endpoint, but we will not describe it as an Attack Discovery connector until that path has been tested end to end.

## What was measured?

The live rehearsal measured counts and state transitions: 136 events, three final alerts, one potential discovery, 12 correlated events, five accounts, ₹11.6 lakh fixture value, and one completed hold-gated workflow. The local deterministic benchmark is not end-to-end latency and excludes Elastic, model, network, and UI time.

## How is the evidence ledger secure?

The prototype provides tamper evidence, not immutable storage. Each block includes the prior hash; the standalone verifier detects alteration. S3 Object Lock and KMS signing remain production/event stretch integrations and must not be claimed until demonstrated.

## Did you build this before the hackathon?

We built and tested a private rehearsal to understand the platform and de-risk the architecture, as the AMA explicitly allows experimentation. The judged implementation is rebuilt from the event start in the official repository, and we disclose what existed before versus what was built during the event.

