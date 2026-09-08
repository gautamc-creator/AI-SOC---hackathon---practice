PYTHON ?= python3
LANGUAGES ?= hi-IN,mr-IN,ta-IN,te-IN,bn-IN

.PHONY: demo benchmark seed validate verify-ingest create-rule validate-detection-queries validate-rules validate-alerts run-attack-discovery capture-attack-discovery review-discovery case-preview case-live workflow-live workflow-agent-test workflow-human-gate-test workflow-e2e-test dashboard-live classify envelope exposure-query review compliance notify warroom verify tamper-verify timeline mitre topology dispatch brief-live brief-adversarial brief-verify localise bedrock-probe serve site deploy-vercel test test-adversarial eval-compare field-provenance scan-injection clean

demo:
	$(PYTHON) scripts/golden_path.py

benchmark:
	$(PYTHON) scripts/benchmark.py --runs $(or $(RUNS),5)

seed:
	$(PYTHON) data/generator/generate.py
	$(PYTHON) elastic/seed.py

validate:
	$(PYTHON) elastic/validate.py

verify-ingest:
	$(PYTHON) elastic/verify_ingest.py

create-rule:
	$(PYTHON) elastic/create_rule.py

validate-detection-queries:
	$(PYTHON) elastic/validate_detection_queries.py

validate-rules:
	$(PYTHON) elastic/validate_rules.py

validate-alerts:
	$(PYTHON) elastic/validate_alerts.py

run-attack-discovery:
	$(PYTHON) elastic/run_attack_discovery.py

capture-attack-discovery:
	$(PYTHON) elastic/capture_attack_discovery.py $(EXECUTION_UUID)

review-discovery:
	$(PYTHON) workflow/review_discovery.py

case-preview:
	$(PYTHON) elastic/create_case.py

case-live:
	$(PYTHON) elastic/create_case.py --live

workflow-live:
	$(PYTHON) elastic/create_workflow.py

workflow-agent-test:
	$(PYTHON) elastic/test_agent_workflow.py

workflow-human-gate-test:
	$(PYTHON) elastic/test_human_gate.py

workflow-e2e-test:
	$(PYTHON) elastic/test_full_workflow.py --live

dashboard-live:
	$(PYTHON) elastic/create_dashboard.py

classify:
	$(PYTHON) workflow/classify.py

envelope:
	$(PYTHON) workflow/gather_evidence.py

exposure-query:
	$(PYTHON) elastic/esql/render_exposure_query.py

review:
	$(PYTHON) approvals/review.py --decision hold

compliance:
	$(PYTHON) compliance/generate.py

notify:
	$(PYTHON) notifications/prepare.py

warroom:
	$(PYTHON) warroom/prepare.py
	@echo "Open http://localhost:8000/warroom/ after running: $(PYTHON) -m http.server 8000"

verify:
	$(PYTHON) ledger/verify.py artifacts/evidence-ledger.json

tamper-verify:
	$(PYTHON) ledger/verify.py artifacts/evidence-ledger.tampered.json

test:
	$(PYTHON) -m unittest discover -s tests -v

test-adversarial:
	$(PYTHON) -m unittest tests.test_adversarial -v

eval-compare:
	$(PYTHON) eval/run_comparison.py

field-provenance:
	$(PYTHON) compliance/field_provenance.py

scan-injection:
	$(PYTHON) workflow/scan_for_injection.py

timeline:
	$(PYTHON) workflow/timeline.py

mitre:
	$(PYTHON) workflow/mitre_map.py

topology:
	$(PYTHON) workflow/topology.py

dispatch:
	$(PYTHON) notifications/dispatch.py

# --- AWS Bedrock -------------------------------------------------------------
# bedrock-probe lists what this account can actually call and proves one invocation.
bedrock-probe:
	$(PYTHON) llm/bedrock.py

# The constrained brief used in the demo, then re-verified into the War Room.
brief-live:
	$(PYTHON) llm/grounded_brief.py --mode grounded
	$(PYTHON) warroom/prepare.py

# Deliberate adversarial probe: proves the grounding verifier fires on a loose prompt.
brief-adversarial:
	$(PYTHON) llm/grounded_brief.py --mode adversarial
	$(PYTHON) warroom/prepare.py

# Re-verify a captured brief with no network call.
brief-verify:
	$(PYTHON) llm/grounded_brief.py --offline

# --- Sarvam AI ---------------------------------------------------------------
localise:
	$(PYTHON) sarvam/translate.py --languages $(LANGUAGES)
	$(PYTHON) warroom/prepare.py

# --- local cockpit -----------------------------------------------------------
# The War Room fetches JSON, so it must be served over HTTP, not opened as a file.
serve:
	@echo "War Room: http://localhost:$(or $(PORT),8000)/warroom/"
	$(PYTHON) -m http.server $(or $(PORT),8000)

# --- static deploy (free tier) ----------------------------------------------
# The War Room needs no server, so it deploys as static files: no cold start to stall
# a demo, and nothing to keep running between rehearsals.
site:
	$(PYTHON) scripts/build_site.py
	@cp deploy/vercel.json site/vercel.json
	@echo "Staged site/ — preview locally with: $(PYTHON) -m http.server 8001 --directory site"

deploy-vercel: site
	npx vercel deploy --prod site

clean:
	rm -rf artifacts site
