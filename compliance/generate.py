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
    common = {"status": "DRAFT — HUMAN REVIEW REQUIRED", "synthetic_data_notice": "Synthetic rehearsal data only. Do not submit this artifact to a regulator.", "incident_id": report["incident_id"], "occurrence_start_timestamp_utc": report["occurrence_start_timestamp_utc"], "first_observed_timestamp_utc": report["first_observed_timestamp_utc"], "classification": report["classification"], "affected_asset": report["affected_asset"], "evidence_event_ids": report["evidence_event_ids"]}
    write("rbi-daksh-information-pack.json", {**common, "purpose": "Information pack for an authorised regulated entity preparing the applicable RBI incident/fraud report.", "format_boundary": "This is not a validated Annex 1 or DAKSH screen/bulk-upload format. The authorised entity must choose and complete the applicable current RBI workflow.", "exposure_inr": report["deterministic_exposure_inr"], "submission_status": "NOT SUBMITTED"})
    write("cert-in-incident-form-draft.json", {**common, "purpose": "Draft aligned to fields in CERT-In's public Incident Reporting Form; review and complete before any real submission.", "reporting_party": {"relationship_to_incident": "AFFECTED ENTITY (synthetic rehearsal)", "reporter_name_and_role": "REQUIRED BEFORE SUBMISSION", "organisation_name": "REQUIRED BEFORE SUBMISSION", "contact_number": "REQUIRED BEFORE SUBMISSION", "email": "REQUIRED BEFORE SUBMISSION", "address": "REQUIRED BEFORE SUBMISSION"}, "incident_type": "Attacks or incident affecting Digital Payment systems", "mission_critical_system": {"value": "Yes — synthetic Tier 1 payment-service fixture", "brief_details": "Synthetic UPI payment gateway service."}, "affected_system": {"host": report["affected_asset"], "domain_or_url": "NOT OBSERVED IN FIXTURE", "ip_address": "10.42.0.11 (synthetic)", "operating_system": "NOT OBSERVED IN FIXTURE", "cloud_or_make_model": "NOT OBSERVED IN FIXTURE", "location": "NOT APPLICABLE — synthetic", "network_or_isp": "NOT OBSERVED IN FIXTURE"}, "incident_description": report["classification"], "symptoms_observed": ["Repeated failed privileged authentication", "Subsequent privileged login", "Outbound connection to unapproved synthetic destination", "Five anomalous synthetic UPI transfers"], "technical_information": {"source_ip": "198.51.100.42 (documentation address)", "destination_ip": "203.0.113.77 (documentation address)", "evidence_envelope": "evidence-envelope.json"}, "actions_taken": "No containment was executed in this rehearsal. Human review requested.", "submission_status": "NOT SUBMITTED"})
    ip_id = f"ipv4-addr--{uuid5(NAMESPACE_URL, report['incident_id'] + ':source-ip')}"
    observed_id = f"observed-data--{uuid5(NAMESPACE_URL, report['incident_id'] + ':observed')}"
    write("stix-2.1-draft.json", {"type": "bundle", "id": f"bundle--{uuid5(NAMESPACE_URL, report['incident_id'] + ':bundle')}", "objects": [{"type": "ipv4-addr", "spec_version": "2.1", "id": ip_id, "value": "198.51.100.42"}, {"type": "observed-data", "spec_version": "2.1", "id": observed_id, "created": now, "modified": now, "first_observed": report["occurrence_start_timestamp_utc"], "last_observed": report["first_observed_timestamp_utc"], "number_observed": 1, "object_refs": [ip_id], "labels": ["synthetic", "human-review-required"]}, {"type": "indicator", "spec_version": "2.1", "id": f"indicator--{uuid5(NAMESPACE_URL, report['incident_id'])}", "created": now, "modified": now, "name": "VIGIL synthetic payment-service investigation lead", "description": "Synthetic prototype indicator generated for analyst review; not a CERT-In filing or asserted compromise.", "pattern_type": "stix", "pattern": "[ipv4-addr:value = '198.51.100.42']", "valid_from": now, "labels": ["synthetic", "human-review-required", "potential-attack-discovery"]}], "notice": "Optional STIX 2.1 interoperability draft. Validate with a STIX validator and verify recipient requirements before use."})
    print("Created RBI DAKSH, CERT-In and STIX review-only drafts.")

if __name__ == "__main__":
    main()
