#!/usr/bin/env python3
"""Upsert and read back the VIGIL evidence dashboard using Kibana's typed API."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ID = "vigil-evidence-dashboard"
EXPECTED_PANEL_TYPES = ["markdown", "vis", "vis", "vis", "vis"]


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")

    definition = json.loads(
        (ROOT / "elastic/dashboards/vigil-evidence-dashboard.json").read_text(encoding="utf-8")
    )
    headers = {"kbn-xsrf": "vigil-local-prototype"}
    saved = json.loads(
        seed.request(
            "PUT",
            f"/api/dashboards/{DASHBOARD_ID}",
            json.dumps(definition).encode(),
            base_url=kibana_url,
            extra_headers=headers,
        )
    )
    verified = json.loads(
        seed.request("GET", f"/api/dashboards/{DASHBOARD_ID}", base_url=kibana_url)
    )

    dashboard = verified.get("data", {})
    panel_types = [panel.get("type") for panel in dashboard.get("panels", [])]
    if verified.get("id") != DASHBOARD_ID:
        raise RuntimeError(f"Dashboard read-back returned unexpected ID: {verified.get('id')}")
    if dashboard.get("title") != definition["title"]:
        raise RuntimeError("Dashboard title did not survive read-back.")
    if panel_types != EXPECTED_PANEL_TYPES:
        raise RuntimeError(f"Dashboard panels did not survive read-back: {panel_types}")
    if verified.get("warnings"):
        raise RuntimeError(f"Dashboard API returned warnings: {json.dumps(verified['warnings'], indent=2)}")

    proof = {
        "status": "PASS — LIVE KIBANA DASHBOARD",
        "id": DASHBOARD_ID,
        "title": dashboard["title"],
        "panel_count": len(panel_types),
        "panel_types": panel_types,
        "api": "Kibana typed Dashboards API",
        "scope": "Synthetic rehearsal evidence; fixed scenario time range; no containment or submission action.",
    }
    (ROOT / "artifacts/dashboard-proof.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))
    print(f"Open: {kibana_url}/app/dashboards#/view/{DASHBOARD_ID}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
