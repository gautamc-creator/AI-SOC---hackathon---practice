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
    bank_context = read_ndjson(artifacts / "bank-context.ndjson")
    classification = json.loads((artifacts / "classification.json").read_text(encoding="utf-8"))
    envelope = json.loads((artifacts / "evidence-envelope.json").read_text(encoding="utf-8"))
    evidence_ids = set(envelope["evidence_event_ids"])
    evidence = [row for row in events if row["_id"] in evidence_ids]
    hosts = sorted({row.get("host", {}).get("name") for row in evidence if row.get("host", {}).get("name")})
    if len(hosts) != 1:
        raise RuntimeError(f"Expected one affected host in the sealed evidence; found {hosts}.")
    affected_asset = hosts[0]
    context_matches = [row for row in bank_context if row.get("host.name") == affected_asset]
    if len(context_matches) != 1:
        raise RuntimeError(f"Expected one bank-context row for {affected_asset}; found {len(context_matches)}.")
    affected_service = context_matches[0]["vigil.bank.service"]
    occurrence_start = min(row["@timestamp"] for row in evidence)
    first_observed = min(row["event"]["created"] for row in evidence)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    upi_total = sum(row.get("vigil", {}).get("transaction", {}).get("amount", 0) for row in evidence)
    expected_exposure = truth["hero"]["expected_exposure_inr"]
    if upi_total != expected_exposure:
        raise RuntimeError(
            f"Evidence-derived exposure INR {upi_total:,} does not match the fixture answer key "
            f"INR {expected_exposure:,}; refusing to generate a report."
        )
    discovery_path = artifacts / "attack-discovery-baseline.json"
    discovery: dict | None = None
    claim_review_path = artifacts / "attack-discovery-claim-review.json"
    claim_review = json.loads(claim_review_path.read_text(encoding="utf-8")) if claim_review_path.exists() else None
    if discovery_path.exists():
        discovery_data = json.loads(discovery_path.read_text(encoding="utf-8"))
        discoveries = discovery_data.get("response", {}).get("data", [])
        if discoveries:
            discovery = discoveries[0]

    report = {
        "status": "DRAFT — HUMAN REVIEW REQUIRED",
        "prototype_notice": "Synthetic data only. This artifact is not filed with RBI, CERT-In, or any regulator.",
        "incident_id": "VIGIL-2026-09-06-001",
        "classification": classification["classification"],
        "classification_method": classification["method"],
        "occurrence_start_timestamp_utc": occurrence_start,
        "first_observed_timestamp_utc": first_observed,
        "cert_in_notice_anchor_utc": generated_at,
        "regulatory_timing_note": "Prototype timing anchors only. Confirm the regulated entity's current RBI and CERT-In obligations before any real-world use.",
        "affected_asset": affected_asset,
        "affected_service": affected_service,
        "deterministic_exposure_inr": upi_total,
        "observed_suspicious_upi_total_inr": upi_total,
        "evidence_event_ids": [row["_id"] for row in evidence],
        "evidence_envelope": {"artifact": "evidence-envelope.json", "evidence_set_hash": envelope["integrity"]["evidence_set_hash"]},
        "attack_discovery": ({
            "label": discovery_data["label"],
            "generation_uuid": discovery["generation_uuid"],
            "discovery_id": discovery["id"],
            "title": discovery["title"],
            "summary": discovery["summary_markdown"],
            "mitre_attack_tactics": discovery.get("mitre_attack_tactics", []),
            "interpretation": "AI-generated potential attack narrative. It is an investigation lead, not confirmation of compromise, fraud, or regulatory reportability.",
        } if discovery else {"status": "Not yet captured; local fixture mode only."}),
        "attack_discovery_claim_review": claim_review or {
            "status": "NOT_RUN",
            "safe_interpretation": "Human review is required before relying on generated claims.",
        },
        "recommended_human_action": "Review the evidence, contain the affected service if authorised, and submit the applicable regulatory reports through approved channels.",
        "reporting_pack": {
            "cert_in": "Information draft aligned to the public CERT-In incident-reporting form; required reporter and organisation fields remain intentionally blank.",
            "rbi_daksh": "Information pack only, not a validated RBI Annex 1/DAKSH submission format; no portal automation or submission occurs.",
        },
    }
    (artifacts / "incident-report-draft.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    chain: list[dict] = []
    append_block(chain, "incident_detected", {"incident_id": report["incident_id"], "evidence_ids": report["evidence_event_ids"]}, first_observed)
    append_block(chain, "classification_completed", {"artifact": "classification.json", "method": classification["method"]}, generated_at)
    append_block(chain, "evidence_enveloped", {"artifact": "evidence-envelope.json", "evidence_set_hash": envelope["integrity"]["evidence_set_hash"]}, generated_at)
    if discovery:
        append_block(chain, "attack_discovery_generated", {
            "source": "Elastic Security Attack Discovery",
            "generation_uuid": discovery["generation_uuid"], "discovery_id": discovery["id"],
            "label": discovery_data["label"],
        }, generated_at)
    elif (
        claim_review
        and claim_review.get("source") == "Elastic Security Attack Discovery captured rehearsal output"
        and claim_review.get("discovery_count", 0) > 0
    ):
        # Static rebuilds retain the reviewed public proof but not the private raw
        # Attack Discovery response or its identifiers. Seal that distinction.
        append_block(chain, "attack_discovery_review_captured", {
            "source": claim_review["source"],
            "discovery_count": claim_review["discovery_count"],
            "findings_count": len(claim_review.get("findings", [])),
            "raw_discovery_published": False,
        }, generated_at)
    append_block(chain, "exposure_calculated", {"method": "deterministic_lookup_context", "amount_inr": report["deterministic_exposure_inr"]}, generated_at)
    append_block(chain, "human_review_requested", {"status": report["status"], "action": report["recommended_human_action"]}, generated_at)
    append_block(chain, "report_drafted", {"artifact": "incident-report-draft.json", "submission": "not submitted"}, generated_at)
    (artifacts / "evidence-ledger.json").write_text(json.dumps(chain, indent=2) + "\n", encoding="utf-8")

    html = f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>{report['incident_id']}</title>
<style>body{{font-family:system-ui;max-width:900px;margin:40px auto;line-height:1.5}}.warning{{background:#fff3cd;padding:16px;border-left:5px solid #b7791f}}code{{background:#f1f5f9;padding:2px 4px}}</style></head><body>
<div class=\"warning\"><strong>{report['status']}</strong><br>{report['prototype_notice']}</div>
<h1>VIGIL incident reporting draft</h1><p><strong>Incident:</strong> {report['incident_id']}</p>
<p><strong>Classification:</strong> {report['classification']}</p><p><strong>Occurrence start:</strong> {occurrence_start}</p><p><strong>First observed:</strong> {first_observed}</p>
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
