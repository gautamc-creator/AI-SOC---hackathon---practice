#!/usr/bin/env python3
"""Preview or create one Elastic Security case from the captured VIGIL discovery."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OWNER = "securitySolution"


def load_context() -> tuple[dict, dict, dict]:
    report = json.loads((ARTIFACTS / "incident-report-draft.json").read_text(encoding="utf-8"))
    capture = json.loads((ARTIFACTS / "attack-discovery-baseline.json").read_text(encoding="utf-8"))
    review = json.loads((ARTIFACTS / "attack-discovery-claim-review.json").read_text(encoding="utf-8"))
    discoveries = capture.get("response", {}).get("data", [])
    if not discoveries:
        raise RuntimeError("No captured Attack Discovery finding is available.")
    return report, discoveries[0], review


def case_body(report: dict, discovery: dict, review: dict) -> dict:
    flagged = ", ".join(item["phrase"] for item in review.get("findings", [])) or "none"
    description = f"""## Prototype boundary
Synthetic rehearsal only. Potential incident; not confirmed compromise or fraud. No containment or regulatory submission is authorised by this case.

## Attack Discovery lead
{discovery.get('summary_markdown', '')}

## VIGIL grounded context
- Incident: {report['incident_id']}
- Asset: {report['affected_asset']}
- Fixture exposure: INR {report['deterministic_exposure_inr']}
- Evidence events: {len(report['evidence_event_ids'])}
- AI claim-safety review: {review['status']}
- Flagged certainty language: {flagged}

## Human gate
Validate the source alerts, transaction context, impact, reportability, and authority before any response action.
"""
    return {
        "title": "[VIGIL rehearsal] Potential credential compromise with anomalous UPI activity",
        "description": description,
        "tags": ["VIGIL", "synthetic", "attack-discovery", "human-review-required"],
        "connector": {"id": "none", "name": "none", "type": ".none", "fields": None},
        "settings": {"syncAlerts": True},
        "owner": OWNER,
        "severity": "high",
    }


def component_alerts(alert_ids: list[str]) -> list[dict]:
    body = {
        "size": len(alert_ids),
        "_source": ["kibana.alert.rule.uuid", "kibana.alert.rule.name"],
        "query": {"ids": {"values": alert_ids}},
    }
    response = json.loads(seed.request("POST", "/.alerts-security.alerts-*/_search", json.dumps(body).encode()))
    return [
        {
            "alert_id": hit["_id"],
            "index": hit["_index"],
            "rule": {
                "id": hit["_source"].get("kibana.alert.rule.uuid"),
                "name": hit["_source"].get("kibana.alert.rule.name"),
            },
        }
        for hit in response.get("hits", {}).get("hits", [])
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Create the case and attach alerts in Kibana.")
    args = parser.parse_args()
    report, discovery, review = load_context()
    body = case_body(report, discovery, review)
    preview = {
        "status": "PREVIEW — NOT CREATED" if not args.live else "LIVE CREATE REQUESTED",
        "source_discovery_id": discovery.get("id"),
        "component_alert_ids": discovery.get("alert_ids", []),
        "case": body,
    }
    (ARTIFACTS / "elastic-case-preview.json").write_text(json.dumps(preview, indent=2) + "\n", encoding="utf-8")
    if not args.live:
        print("Wrote artifacts/elastic-case-preview.json; no Elastic case was created.")
        return

    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    headers = {"kbn-xsrf": "vigil-local-prototype"}
    created = json.loads(seed.request("POST", "/api/cases", json.dumps(body).encode(), base_url=kibana_url, extra_headers=headers))
    alerts = component_alerts(discovery.get("alert_ids", []))
    for alert in alerts:
        comment = {
            "type": "alert",
            "alertId": alert["alert_id"],
            "index": alert["index"],
            "owner": OWNER,
            "rule": alert["rule"],
        }
        seed.request(
            "POST", f"/api/cases/{created['id']}/comments", json.dumps(comment).encode(),
            base_url=kibana_url, extra_headers=headers,
        )
    proof = {
        "status": "CREATED IN ELASTIC SECURITY — SYNTHETIC REHEARSAL",
        "case_id": created["id"],
        "title": created["title"],
        "owner": created["owner"],
        "attached_component_alerts": len(alerts),
        "expected_component_alerts": len(discovery.get("alert_ids", [])),
        "human_review_required": True,
    }
    (ARTIFACTS / "elastic-case-live.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
