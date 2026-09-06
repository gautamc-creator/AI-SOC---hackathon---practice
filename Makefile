PYTHON ?= python3

.PHONY: demo seed validate create-rule validate-alerts run-attack-discovery capture-attack-discovery classify envelope review compliance notify warroom verify tamper-verify test clean

demo:
	$(PYTHON) scripts/golden_path.py

seed:
	$(PYTHON) data/generator/generate.py
	$(PYTHON) elastic/seed.py

validate:
	$(PYTHON) elastic/validate.py

create-rule:
	$(PYTHON) elastic/create_rule.py

validate-alerts:
	$(PYTHON) elastic/validate_alerts.py

run-attack-discovery:
	$(PYTHON) elastic/run_attack_discovery.py

capture-attack-discovery:
	$(PYTHON) elastic/capture_attack_discovery.py $(EXECUTION_UUID)

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
