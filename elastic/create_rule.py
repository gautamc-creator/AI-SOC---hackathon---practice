#!/usr/bin/env python3
"""Create or update VIGIL's behavior-based rehearsal detection rules."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
LEGACY_RULE_ID = "vigil-synthetic-payment-compromise-v1"


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env to the Kibana endpoint from Connection details.")
    results = []
    for path in sorted((ROOT / "elastic/rules").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        try:
            seed.request(
                "GET", f"/api/detection_engine/rules?rule_id={payload['rule_id']}",
                base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
            )
            method = "PUT"
        except RuntimeError as error:
            if "(404)" not in str(error):
                raise
            method = "POST"
        response = seed.request(
            method, "/api/detection_engine/rules", json.dumps(payload).encode(),
            base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
        )
        saved = json.loads(response)
        results.append({"file": path.name, "operation": "created" if method == "POST" else "updated", "rule_id": saved.get("rule_id"), "id": saved.get("id"), "enabled": saved.get("enabled")})
    legacy = {"rule_id": LEGACY_RULE_ID, "status": "not_found"}
    try:
        existing = json.loads(seed.request(
            "GET", f"/api/detection_engine/rules?rule_id={LEGACY_RULE_ID}",
            base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
        ))
        if existing.get("enabled"):
            seed.request(
                "POST", "/api/detection_engine/rules/_bulk_action",
                json.dumps({"action": "disable", "ids": [existing["id"]]}).encode(),
                base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
            )
            legacy = {"rule_id": LEGACY_RULE_ID, "status": "disabled", "id": existing["id"]}
        else:
            legacy = {"rule_id": LEGACY_RULE_ID, "status": "already_disabled", "id": existing["id"]}
    except RuntimeError as error:
        if "(404)" not in str(error):
            raise
    print(json.dumps({"rules": results, "legacy_rule": legacy}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
