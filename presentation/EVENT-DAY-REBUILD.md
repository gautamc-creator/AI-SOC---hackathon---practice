# Event-day rebuild plan

The rehearsal repository is a learning and validation asset. The judged implementation starts on 18 September.

## The minimum winning vertical slice

1. Ingest the fixed synthetic scenario into the event Elastic project.
2. Recreate the ingest pipeline, lookup context, and three behaviour rules.
3. Validate an AWS-hosted LLM path and record the exact model, region, connector/inference identifier, and harmless test output.
4. Run Attack Discovery and save one potential discovery.
5. Recreate the dashboard and ES|QL payment-context pivot.
6. Recreate the case + Agent Builder + human `hold` workflow.
7. Generate the human-review regulatory draft.
8. Run genuine/tampered ledger verification.
9. Update README, event build log, deck numbers, and backup recording.

## Suggested ownership for three active builders

| Builder | Owns |
|---|---|
| A | Elastic data, mappings, detection rules, Attack Discovery, dashboard. |
| B | AWS-hosted LLM proof, Agent Builder/Workflow, integration evidence. |
| C | Draft artifact, ledger/verifier, README, build log, demo capture. |

All builders review the final 90-second path. One person speaks, one drives, one watches timing and recovery.

## Required event evidence

- First and final commit timestamps.
- Elastic project/version and relevant feature settings.
- AWS model/region and connector or endpoint evidence with secrets removed.
- Fresh counts from the judged environment.
- Workflow execution and case IDs.
- Test output and tamper-failure output.
- Clear synthetic-data declaration.

