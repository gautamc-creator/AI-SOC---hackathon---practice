PYTHON ?= python3

.PHONY: demo benchmark seed validate verify-ingest create-rule validate-detection-queries validate-rules validate-alerts run-attack-discovery capture-attack-discovery review-discovery case-preview case-live classify envelope review compliance notify warroom verify tamper-verify test clean

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

classify:
	$(PYTHON) workflow/classify.py

envelope:
	$(PYTHON) workflow/gather_evidence.py

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

clean:
	rm -rf artifacts
