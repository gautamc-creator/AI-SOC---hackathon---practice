#!/usr/bin/env python3
"""Generate review-only compliance artefacts from a VIGIL incident draft."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

ROOT = Path(__file__).resolve().parents[1]

def write(name: str, value: dict) -> None:
    (ROOT / "artifacts" / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def main() -> None:
    report = json.loads((ROOT / "artifacts/incident-report-draft.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    common = {"status": "DRAFT — HUMAN REVIEW REQUIRED", "synthetic_data_notice": "Synthetic rehearsal data only. Do not submit this artifact to a regulator.", "incident_id": report["incident_id"], "detection_timestamp_utc": report["detection_timestamp_utc"], "classification": report["classification"], "affected_asset": report["affected_asset"], "evidence_event_ids": report["evidence_event_ids"]}
    write("rbi-daksh-submission-draft.json", {**common, "purpose": "Information pack for an authorised reviewer preparing an RBI DAKSH filing.", "reporting_clock_note": "Prototype timing anchor only. Confirm the current RBI filing workflow and deadline before any real use.", "exposure_inr": report["deterministic_exposure_inr"], "submission_status": "NOT SUBMITTED"})
    write("cert-in-notification-draft.json", {**common, "purpose": "Information pack for an authorised reviewer preparing a CERT-In notification.", "notice_anchor_utc": report["cert_in_notice_anchor_utc"], "submission_status": "NOT SUBMITTED"})
    write("stix-2.1-draft.json", {"type": "bundle", "id": f"bundle--{uuid5(NAMESPACE_URL, report['incident_id'] + ':bundle')}", "objects": [{"type": "indicator", "spec_version": "2.1", "id": f"indicator--{uuid5(NAMESPACE_URL, report['incident_id'])}", "created": now, "modified": now, "name": "VIGIL synthetic payment-service investigation lead", "description": "Synthetic prototype indicator generated for analyst review; not a CERT-In filing or asserted compromise.", "pattern_type": "stix", "pattern": "[x-vigil:incident_id = 'VIGIL-2026-09-06-001']", "valid_from": now, "labels": ["synthetic", "human-review-required", "potential-attack-discovery"]}], "notice": "Optional interoperability draft. Verify any current recipient format requirements before use."})
    print("Created RBI DAKSH, CERT-In and STIX review-only drafts.")

if __name__ == "__main__":
    main()
