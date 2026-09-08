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

def read_ndjson(name: str) -> list[dict]:
    path = ROOT / "artifacts" / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def main() -> None:
    report = json.loads((ROOT / "artifacts/incident-report-draft.json").read_text(encoding="utf-8"))
    evidence_ids = set(report["evidence_event_ids"])
    evidence = [row for row in read_ndjson("events.ndjson") if row.get("_id") in evidence_ids]
    context_rows = [row for row in read_ndjson("bank-context.ndjson") if row.get("host.name") == report["affected_asset"]]
    if len(context_rows) != 1:
        raise RuntimeError(f"Expected exactly one bank-context row for {report['affected_asset']}.")
    context = context_rows[0]
    actions: dict[tuple[str, str], int] = {}
    for event in evidence:
        key = (event.get("event", {}).get("action", "unknown"), event.get("event", {}).get("outcome", "unknown"))
        actions[key] = actions.get(key, 0) + 1
    symptoms = [f"{count} {action}/{outcome} event(s)" for (action, outcome), count in sorted(actions.items())]
    source_ips = sorted({event.get("source", {}).get("ip") for event in evidence if event.get("source", {}).get("ip")})
    destination_ips = sorted({event.get("destination", {}).get("ip") for event in evidence if event.get("destination", {}).get("ip")})
    external_source_ips = sorted({event.get("source", {}).get("ip") for event in evidence
                                  if event.get("source", {}).get("ip")
                                  and event.get("vigil", {}).get("security", {}).get("source_zone") == "external"})
    regulated_channel = context.get("vigil.bank.regulated_channel")
    incident_type = (
        "Attacks or incidents affecting digital-payment systems"
        if regulated_channel in {"UPI", "IMPS", "NEFT", "RTGS"}
        else "Unauthorised access to IT systems or data"
    )
    criticality = context.get("vigil.bank.criticality", "not_observed")
    mission_critical = criticality == "mission_critical"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    common = {"status": "DRAFT — HUMAN REVIEW REQUIRED", "synthetic_data_notice": "Synthetic rehearsal data only. Do not submit this artifact to a regulator.", "incident_id": report["incident_id"], "occurrence_start_timestamp_utc": report["occurrence_start_timestamp_utc"], "first_observed_timestamp_utc": report["first_observed_timestamp_utc"], "classification": report["classification"], "affected_asset": report["affected_asset"], "evidence_event_ids": report["evidence_event_ids"]}
    write("rbi-daksh-information-pack.json", {**common, "purpose": "Information pack for an authorised regulated entity preparing the applicable RBI incident/fraud report.", "format_boundary": "This is not a validated Annex 1 or DAKSH screen/bulk-upload format. The authorised entity must choose and complete the applicable current RBI workflow.", "exposure_inr": report["deterministic_exposure_inr"], "submission_status": "NOT SUBMITTED"})
    write("cert-in-incident-form-draft.json", {**common, "purpose": "Draft aligned to fields in CERT-In's public Incident Reporting Form; review and complete before any real submission.", "reporting_party": {"relationship_to_incident": "AFFECTED ENTITY (synthetic rehearsal)", "reporter_name_and_role": "REQUIRED BEFORE SUBMISSION", "organisation_name": "REQUIRED BEFORE SUBMISSION", "contact_number": "REQUIRED BEFORE SUBMISSION", "email": "REQUIRED BEFORE SUBMISSION", "address": "REQUIRED BEFORE SUBMISSION"}, "incident_type": incident_type, "incident_type_provenance": f"Deterministic mapping from bank context regulated channel: {regulated_channel or 'not observed'}.", "mission_critical_system": {"value": "Yes" if mission_critical else "No / requires analyst confirmation", "brief_details": f"{context.get('vigil.bank.service', 'Service not observed')} ({criticality})."}, "affected_system": {"host": report["affected_asset"], "domain_or_url": "NOT OBSERVED IN FIXTURE", "ip_address": "NOT OBSERVED IN FIXTURE", "operating_system": "NOT OBSERVED IN FIXTURE", "cloud_or_make_model": "NOT OBSERVED IN FIXTURE", "location": "NOT APPLICABLE — synthetic", "network_or_isp": "NOT OBSERVED IN FIXTURE"}, "incident_description": report["classification"], "symptoms_observed": symptoms, "technical_information": {"source_ips": source_ips, "external_source_ips": external_source_ips, "destination_ips": destination_ips, "evidence_envelope": "evidence-envelope.json"}, "actions_taken": "No containment was executed in this rehearsal. Human review requested.", "submission_status": "NOT SUBMITTED"})
    indicator_ip = external_source_ips[0] if external_source_ips else (source_ips[0] if source_ips else None)
    if not indicator_ip:
        raise RuntimeError("No source IP is present in the sealed evidence; refusing to fabricate a STIX indicator.")
    ip_id = f"ipv4-addr--{uuid5(NAMESPACE_URL, report['incident_id'] + ':source-ip')}"
    observed_id = f"observed-data--{uuid5(NAMESPACE_URL, report['incident_id'] + ':observed')}"
    write("stix-2.1-draft.json", {"type": "bundle", "id": f"bundle--{uuid5(NAMESPACE_URL, report['incident_id'] + ':bundle')}", "objects": [{"type": "ipv4-addr", "spec_version": "2.1", "id": ip_id, "value": indicator_ip}, {"type": "observed-data", "spec_version": "2.1", "id": observed_id, "created": now, "modified": now, "first_observed": report["occurrence_start_timestamp_utc"], "last_observed": report["first_observed_timestamp_utc"], "number_observed": 1, "object_refs": [ip_id], "labels": ["synthetic", "human-review-required"]}, {"type": "indicator", "spec_version": "2.1", "id": f"indicator--{uuid5(NAMESPACE_URL, report['incident_id'])}", "created": now, "modified": now, "name": "VIGIL synthetic payment-service investigation lead", "description": "Synthetic prototype indicator generated for analyst review; not a CERT-In filing or asserted compromise.", "pattern_type": "stix", "pattern": f"[ipv4-addr:value = '{indicator_ip}']", "valid_from": now, "labels": ["synthetic", "human-review-required", "potential-attack-discovery"]}], "notice": "Optional STIX 2.1 interoperability draft. Validate with a STIX validator and verify recipient requirements before use."})
    print("Created RBI DAKSH, CERT-In and STIX review-only drafts.")

if __name__ == "__main__":
    main()
