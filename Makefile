PYTHON ?= python3

.PHONY: demo seed validate create-rule validate-alerts run-attack-discovery capture-attack-discovery verify tamper-verify clean

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

verify:
	$(PYTHON) ledger/verify.py artifacts/evidence-ledger.json

tamper-verify:
	$(PYTHON) ledger/verify.py artifacts/evidence-ledger.tampered.json

clean:
	rm -rf artifacts
