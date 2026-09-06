import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class VIGILContractTests(unittest.TestCase):
    def test_ingest_pipeline_is_present(self):
        self.assertGreaterEqual(len(json.loads((ROOT / "elastic/ingest/vigil-normalize.json").read_text())["processors"]), 3)
    def test_exposure_query_uses_lookup_join(self):
        query = (ROOT / "elastic/esql/exposure_lookup_join.esql").read_text()
        self.assertIn("LOOKUP JOIN vigil-bank-context", query)
        self.assertIn("suspicious_upi_total", query)
    def test_reporting_artifacts_are_review_only_after_demo(self):
        report = ROOT / "artifacts/incident-report-draft.json"
        if not report.exists(): self.skipTest("Run make demo before artifact contract checks")
        content = json.loads(report.read_text())
        self.assertEqual(content["status"], "DRAFT — HUMAN REVIEW REQUIRED")
        self.assertIn("Synthetic", content["prototype_notice"])
    def test_six_step_workflow_sources_exist(self):
        for relative in ("workflow/classify.py", "workflow/gather_evidence.py", "approvals/review.py", "compliance/generate.py", "notifications/prepare.py"):
            self.assertTrue((ROOT / relative).is_file(), relative)
