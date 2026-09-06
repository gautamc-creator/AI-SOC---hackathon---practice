#!/usr/bin/env python3
"""Create a clearly labelled human-review incident reporting draft from fixed evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))
from chain import append_block  # noqa: E402


def read_ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    artifacts = ROOT / "artifacts"
    events = read_ndjson(artifacts / "events.ndjson")
    truth = json.loads((artifacts / "ground-truth.json").read_text(encoding="utf-8"))
    hero_ids = set(truth["hero"]["event_ids"])
    evidence = [row for row in events if row["_id"] in hero_ids]
    detection_time = min(row["@timestamp"] for row in evidence)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    upi_total = sum(row.get("transaction", {}).get("amount", 0) for row in evidence)
    discovery_path = artifacts / "attack-discovery-baseline.json"
    discovery: dict | None = None
    if discovery_path.exists():
        discovery_data = json.loads(discovery_path.read_text(encoding="utf-8"))
        discoveries = discovery_data.get("response", {}).get("data", [])
        if discoveries:
            discovery = discoveries[0]

    report = {
        "status": "DRAFT — HUMAN REVIEW REQUIRED",
        "prototype_notice": "Synthetic data only. This artifact is not filed with RBI, CERT-In, or any regulator.",
        "incident_id": "VIGIL-2026-09-06-001",
        "classification": "Potential credential compromise with anomalous UPI transfers",
        "detection_timestamp_utc": detection_time,
        "cert_in_notice_anchor_utc": generated_at,
        "rbi_daksh_due_basis": "Six-hour prototype timer starts from detection; verify the current filing process before any real-world use.",
        "affected_asset": truth["hero"]["host"],
        "affected_service": "UPI payment gateway",
        "deterministic_exposure_inr": truth["hero"]["expected_exposure_inr"],
        "observed_suspicious_upi_total_inr": upi_total,
        "evidence_event_ids": [row["_id"] for row in evidence],
        "attack_discovery": ({
            "label": discovery_data["label"],
            "generation_uuid": discovery["generation_uuid"],
            "discovery_id": discovery["id"],
            "title": discovery["title"],
            "summary": discovery["summary_markdown"],
            "mitre_attack_tactics": discovery.get("mitre_attack_tactics", []),
            "interpretation": "AI-generated potential attack narrative. It is an investigation lead, not confirmation of compromise, fraud, or regulatory reportability.",
        } if discovery else {"status": "Not yet captured; local fixture mode only."}),
        "recommended_human_action": "Review the evidence, contain the affected service if authorised, and submit the applicable regulatory reports through approved channels.",
        "reporting_pack": {
            "cert_in": "Incident Reporting Form-compatible draft fields are represented in this JSON/HTML artifact.",
            "rbi_daksh": "Submission-pack draft only; no portal automation or submission occurs.",
        },
    }
    (artifacts / "incident-report-draft.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    chain: list[dict] = []
    append_block(chain, "incident_detected", {"incident_id": report["incident_id"], "evidence_ids": report["evidence_event_ids"]}, detection_time)
    if discovery:
        append_block(chain, "attack_discovery_generated", {
            "source": "Elastic Security Attack Discovery",
            "generation_uuid": discovery["generation_uuid"], "discovery_id": discovery["id"],
            "label": discovery_data["label"],
        }, generated_at)
    append_block(chain, "exposure_calculated", {"method": "deterministic_lookup_context", "amount_inr": report["deterministic_exposure_inr"]}, generated_at)
    append_block(chain, "human_review_requested", {"status": report["status"], "action": report["recommended_human_action"]}, generated_at)
    append_block(chain, "report_drafted", {"artifact": "incident-report-draft.json", "submission": "not submitted"}, generated_at)
    (artifacts / "evidence-ledger.json").write_text(json.dumps(chain, indent=2) + "\n", encoding="utf-8")

    html = f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>{report['incident_id']}</title>
<style>body{{font-family:system-ui;max-width:900px;margin:40px auto;line-height:1.5}}.warning{{background:#fff3cd;padding:16px;border-left:5px solid #b7791f}}code{{background:#f1f5f9;padding:2px 4px}}</style></head><body>
<div class=\"warning\"><strong>{report['status']}</strong><br>{report['prototype_notice']}</div>
<h1>VIGIL incident reporting draft</h1><p><strong>Incident:</strong> {report['incident_id']}</p>
<p><strong>Classification:</strong> {report['classification']}</p><p><strong>Detection:</strong> {detection_time}</p>
<p><strong>Deterministic exposure:</strong> ₹{report['deterministic_exposure_inr']:,}</p>
<p><strong>Evidence:</strong> <code>{'</code>, <code>'.join(report['evidence_event_ids'])}</code></p>
<h2>Elastic Attack Discovery</h2><p><strong>{report['attack_discovery'].get('title', 'Not captured')}</strong></p>
<p>{report['attack_discovery'].get('summary', report['attack_discovery'].get('status'))}</p>
<p><em>{report['attack_discovery'].get('label', '')}</em></p>
<p><strong>Interpretation:</strong> {report['attack_discovery'].get('interpretation', '')}</p>
<h2>Required human decision</h2><p>{report['recommended_human_action']}</p>
<h2>Reporting status</h2><p>No reports have been filed. This is a synthetic prototype artifact for review.</p>
</body></html>"""
    (artifacts / "incident-report-draft.html").write_text(html, encoding="utf-8")
    print("Created incident-report-draft.{json,html} and evidence-ledger.json.")


if __name__ == "__main__":
    main()
