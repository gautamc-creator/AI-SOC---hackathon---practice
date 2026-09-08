import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class VIGILContractTests(unittest.TestCase):
    def test_ingest_pipeline_is_present(self):
        self.assertGreaterEqual(len(json.loads((ROOT / "elastic/ingest/vigil-normalize.json").read_text())["processors"]), 3)
        self.assertTrue((ROOT / "elastic/verify_ingest.py").is_file())

    def test_localisation_magnitude_check_requires_an_exact_numeric_token(self):
        from sarvam.translate import check_magnitude_survived, format_indian_integer

        expected = [1_160_000]
        self.assertEqual(
            check_magnitude_survived("कुल 11,60,000 रुपये", expected)["status"],
            "MAGNITUDE_PRESERVED",
        )
        self.assertEqual(
            check_magnitude_survived("মোট 11,600,000 টাকা", expected)["status"],
            "MAGNITUDE_LOST_IN_TRANSLATION",
        )
        self.assertEqual(format_indian_integer(1_160_000), "11,60,000")
        self.assertEqual(format_indian_integer(11_600_000), "1,16,00,000")
    def test_exposure_query_uses_lookup_join(self):
        query = (ROOT / "elastic/esql/exposure_lookup_join.esql").read_text()
        self.assertIn("LOOKUP JOIN vigil-bank-context", query)
        self.assertIn("suspicious_upi_total", query)
        self.assertNotIn("vigil_hero", query)
        self.assertIn("{{host_name}}", query)
        self.assertIn("{{user_name}}", query)
        self.assertNotIn("pay-svc-prod-01", query)
    def test_detection_rules_are_behavior_based(self):
        rules = [json.loads(path.read_text()) for path in sorted((ROOT / "elastic/rules").glob("*.json"))]
        self.assertEqual(len(rules), 7)
        self.assertEqual({rule["type"] for rule in rules}, {"threshold", "eql", "query"})
        for rule in rules:
            self.assertNotIn("vigil_hero", rule["query"])
        attack_script = (ROOT / "elastic/run_attack_discovery.py").read_text()
        self.assertIn("kibana.alert.building_block_type", attack_script)

    def test_new_eval_rules_close_the_disclosed_detection_gaps(self):
        import sys
        sys.path.insert(0, str(ROOT / "eval"))
        from scenarios import scenario_m2_insider_kyc_tampering, scenario_m3_payment_switch_integrity_breach
        from rules_only import evaluate
        m2 = evaluate(scenario_m2_insider_kyc_tampering()["events"])
        m3 = evaluate(scenario_m3_payment_switch_integrity_breach()["events"])
        self.assertTrue(m2["rules"]["rule6"]["fired"])
        self.assertTrue(m3["rules"]["rule7"]["fired"])
        self.assertFalse(json.loads((ROOT / "elastic/rules/06-insider-kyc-tampering.json").read_text())["enabled"])
        self.assertFalse(json.loads((ROOT / "elastic/rules/07-duplicate-settlement.json").read_text())["enabled"])

    def test_rule_queries_contain_no_hardcoded_indicator(self):
        """A rule pinned to the hero's own address, host, user or account cannot generalise.

        This is the failure mode that lets a demo look autonomous while only ever
        matching one fixture, so it is asserted rather than assumed.
        """
        forbidden = ("198.51.100", "203.0.113", "10.42.0", "pay-svc-prod-01",
                     "svc-payments-admin", "ACC-CORP-", "ACC-HNI-", "ACC-RET-",
                     "UPI-HERO-", "UPI-BATCH-2026")
        for path in sorted((ROOT / "elastic/rules").glob("*.json")):
            query = json.loads(path.read_text())["query"]
            for token in forbidden:
                self.assertNotIn(token, query, f"{path.name} pins the literal {token!r}")
    def test_reporting_artifacts_are_review_only_after_demo(self):
        report = ROOT / "artifacts/incident-report-draft.json"
        if not report.exists(): self.skipTest("Run make demo before artifact contract checks")
        content = json.loads(report.read_text())
        self.assertEqual(content["status"], "DRAFT — HUMAN REVIEW REQUIRED")
        self.assertIn("Synthetic", content["prototype_notice"])
        self.assertIn("occurrence_start_timestamp_utc", content)
        self.assertIn("first_observed_timestamp_utc", content)
        events = [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]
        ids = set(content["evidence_event_ids"])
        computed = sum(event.get("vigil", {}).get("transaction", {}).get("amount", 0)
                       for event in events if event["_id"] in ids)
        self.assertEqual(content["deterministic_exposure_inr"], computed)
        certin = json.loads((ROOT / "artifacts/cert-in-incident-form-draft.json").read_text())
        self.assertEqual(certin["affected_system"]["ip_address"], "NOT OBSERVED IN FIXTURE")
        self.assertIn("198.51.100.42", certin["technical_information"]["external_source_ips"])

    def test_rendered_esql_uses_sealed_scope(self):
        artifact = ROOT / "artifacts/exposure-query.json"
        if not artifact.exists(): self.skipTest("Run make demo before rendered-query checks")
        rendered = json.loads(artifact.read_text())
        envelope = json.loads((ROOT / "artifacts/evidence-envelope.json").read_text())
        self.assertEqual(rendered["parameters"]["host"], envelope["scope"]["host"])
        self.assertEqual(rendered["parameters"]["user"], envelope["scope"]["user"])
        self.assertNotIn("{{", rendered["query"])
        self.assertNotIn("vigil_hero", rendered["query"])
    def test_six_step_workflow_sources_exist(self):
        for relative in ("workflow/classify.py", "workflow/gather_evidence.py", "workflow/review_discovery.py", "elastic/create_case.py", "elastic/create_workflow.py", "elastic/test_agent_workflow.py", "elastic/test_human_gate.py", "elastic/test_full_workflow.py", "elastic/create_dashboard.py", "approvals/review.py", "compliance/generate.py", "notifications/prepare.py"):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_dashboard_is_typed_and_claim_safe(self):
        dashboard = json.loads((ROOT / "elastic/dashboards/vigil-evidence-dashboard.json").read_text())
        self.assertEqual(dashboard["title"], "VIGIL — Synthetic payment compromise evidence")
        self.assertEqual([panel["type"] for panel in dashboard["panels"]], ["markdown", "vis", "vis", "vis", "vis"])
        serialized = json.dumps(dashboard)
        self.assertIn("LOOKUP JOIN vigil-bank-context", serialized)
        self.assertIn("Synthetic rehearsal only", serialized)
        self.assertNotIn("confirmed fraud", serialized.lower())
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
        # The hero and decoy are frozen: the exposure figure, the panels and the eval
        # harness all depend on them. The benign background is scalable by --volume, so the
        # total is asserted as the sum of its documented parts rather than a magic number
        # that has to be edited whenever volume changes.
        self.assertEqual((len(hero), len(decoy), amount), (12, 4, 1160000))
        truth = json.loads((ROOT / "artifacts/ground-truth.json").read_text())
        volume = truth["benign_settlement_per_day"]
        normal = [e for e in events if e["_id"].startswith("normal-")]
        settle = [e for e in events if e["_id"].startswith("settle-")]
        self.assertEqual(len(normal), 30 * 4)
        self.assertEqual(len(settle), 30 * volume)
        self.assertEqual(len(events), len(normal) + len(settle) + len(hero) + len(decoy))
        self.assertTrue(all(event.get("labels", {}).get("synthetic") == "true" for event in events))
        upi = [event for event in events if event.get("event", {}).get("action") == "upi_transfer"]
        self.assertTrue(all(event["event"]["category"] == ["web"] for event in upi))
        self.assertTrue(all(event["event"]["type"] == ["access"] for event in upi))
        self.assertTrue(all("transaction" in event and "id" in event["transaction"] for event in upi))
    def test_bank_fields_live_under_the_vendor_namespace(self):
        """ECS reserves the top level, so bank-domain fields must stay under vigil.bank.*.

        A bare top-level ``bank`` object would risk colliding with a future ECS release
        and would misrepresent custom fields as ECS ones.
        """
        events = [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]
        for event in events:
            self.assertNotIn("bank", event, f"{event['_id']} puts bank fields at the ECS top level")
        context = [json.loads(line) for line in (ROOT / "artifacts/bank-context.ndjson").read_text().splitlines() if line]
        for row in context:
            for key in row:
                self.assertFalse(
                    key == "bank" or key.startswith("bank."),
                    f"bank-context key {key!r} is outside the vigil.* namespace",
                )

    def test_bank_enrichment_is_typed_and_separates_hero_from_benign(self):
        """The KYC and AML fields must be explicitly mapped and actually discriminate.

        Dynamic mapping would type customer_tier as text, which cannot back an ES|QL
        ``STATS ... BY`` or a threshold rule; and an AML score that does not separate the
        hero from routine settlement traffic would make the AML rule decorative.
        """
        template = json.loads((ROOT / "elastic/mappings/logs-vigil-security-template.json").read_text())
        bank = template["template"]["mappings"]["properties"]["vigil"]["properties"]["bank"]["properties"]
        self.assertEqual(bank["customer_tier"]["type"], "keyword")
        self.assertEqual(bank["batch_id"]["type"], "keyword")
        self.assertEqual(bank["account_id"]["type"], "keyword")
        self.assertEqual(bank["upi_vpa"]["type"], "keyword")
        self.assertEqual(bank["kyc_verified"]["type"], "boolean")
        self.assertEqual(bank["aml_risk_score"]["type"], "float")

        events = [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]
        scored = [(e, e["vigil"]["bank"]["aml_risk_score"]) for e in events
                  if e.get("vigil", {}).get("bank", {}).get("aml_risk_score") is not None]
        hero_scores = [s for e, s in scored if "vigil_hero" in e.get("tags", [])]
        benign_scores = [s for e, s in scored if "vigil_hero" not in e.get("tags", [])]
        self.assertTrue(hero_scores and benign_scores)
        self.assertGreater(min(hero_scores), max(benign_scores),
                           "the AML score does not separate the hero from benign settlement traffic")
        threshold = json.loads((ROOT / "artifacts/bank-context.ndjson").read_text().splitlines()[0])["vigil.bank.aml_alert_threshold"]
        self.assertGreater(min(hero_scores), threshold)
        self.assertLess(max(benign_scores), threshold)

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
        self.assertIn("do not call tools", workflow)
        self.assertIn("type: waitForInput", workflow)
        self.assertIn("enum: [approve, hold, reject]", workflow)
        self.assertNotIn("/api/endpoint/action/isolate", workflow)
        self.assertIn("HUMAN REVIEW REQUIRED", workflow)
