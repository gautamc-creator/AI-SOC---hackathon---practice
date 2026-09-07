import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class VIGILContractTests(unittest.TestCase):
    def test_ingest_pipeline_is_present(self):
        self.assertGreaterEqual(len(json.loads((ROOT / "elastic/ingest/vigil-normalize.json").read_text())["processors"]), 3)
        self.assertTrue((ROOT / "elastic/verify_ingest.py").is_file())
    def test_exposure_query_uses_lookup_join(self):
        query = (ROOT / "elastic/esql/exposure_lookup_join.esql").read_text()
        self.assertIn("LOOKUP JOIN vigil-bank-context", query)
        self.assertIn("suspicious_upi_total", query)
        self.assertNotIn("vigil_hero", query)
    def test_detection_rules_are_behavior_based(self):
        rules = [json.loads(path.read_text()) for path in sorted((ROOT / "elastic/rules").glob("*.json"))]
        self.assertEqual(len(rules), 3)
        self.assertEqual({rule["type"] for rule in rules}, {"threshold", "eql"})
        for rule in rules:
            self.assertNotIn("vigil_hero", rule["query"])
        attack_script = (ROOT / "elastic/run_attack_discovery.py").read_text()
        self.assertIn("kibana.alert.building_block_type", attack_script)
    def test_reporting_artifacts_are_review_only_after_demo(self):
        report = ROOT / "artifacts/incident-report-draft.json"
        if not report.exists(): self.skipTest("Run make demo before artifact contract checks")
        content = json.loads(report.read_text())
        self.assertEqual(content["status"], "DRAFT — HUMAN REVIEW REQUIRED")
        self.assertIn("Synthetic", content["prototype_notice"])
        self.assertIn("occurrence_start_timestamp_utc", content)
        self.assertIn("first_observed_timestamp_utc", content)
    def test_six_step_workflow_sources_exist(self):
        for relative in ("workflow/classify.py", "workflow/gather_evidence.py", "workflow/review_discovery.py", "elastic/create_case.py", "approvals/review.py", "compliance/generate.py", "notifications/prepare.py"):
            self.assertTrue((ROOT / relative).is_file(), relative)
    def test_data_provenance_is_documented(self):
        provenance = (ROOT / "data/DATA-PROVENANCE.md").read_text()
        self.assertIn("synthetic", provenance.lower())
        self.assertIn("20260906", provenance)
    def test_realism_audit_has_claim_boundaries(self):
        audit = (ROOT / "docs/REALISM-AND-FORMAT-AUDIT.md").read_text()
        self.assertIn("not a universal submission format", audit)
        self.assertIn("not an NPCI/UPI message specification", audit)
    def test_fixture_conformance(self):
        events = [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]
        hero = [event for event in events if "vigil_hero" in event.get("tags", [])]
        decoy = [event for event in events if "vigil_decoy" in event.get("tags", [])]
        amount = sum(event.get("vigil", {}).get("transaction", {}).get("amount", 0) for event in hero)
        self.assertEqual((len(events), len(hero), len(decoy), amount), (136, 12, 4, 1160000))
        self.assertTrue(all(event.get("labels", {}).get("synthetic") == "true" for event in events))
        upi = [event for event in events if event.get("event", {}).get("action") == "upi_transfer"]
        self.assertTrue(all(event["event"]["category"] == ["web"] for event in upi))
        self.assertTrue(all(event["event"]["type"] == ["access"] for event in upi))
        self.assertTrue(all("transaction" in event and "id" in event["transaction"] for event in upi))
    def test_ai_claim_review_is_explicitly_non_adjudicative(self):
        source = (ROOT / "workflow/review_discovery.py").read_text()
        self.assertIn("not an incident verdict", source)
        report = ROOT / "artifacts/attack-discovery-claim-review.json"
        if report.exists():
            review = json.loads(report.read_text())
            self.assertIn(review["status"], {"REVIEW_REQUIRED", "NO_FLAGGED_CERTAINTY_LANGUAGE", "NOT_RUN"})
    def test_candidate_elastic_workflow_stops_at_human_review(self):
        workflow = (ROOT / "elastic/workflows/vigil-human-gated-triage.yaml").read_text()
        self.assertIn("cases.createCase", workflow)
        self.assertIn("cases.addAlerts", workflow)
        self.assertIn("ai.agent", workflow)
        self.assertNotIn("/api/endpoint/action/isolate", workflow)
        self.assertIn("HUMAN REVIEW REQUIRED", workflow)
