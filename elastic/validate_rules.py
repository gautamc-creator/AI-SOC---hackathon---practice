#!/usr/bin/env python3
"""Read-only health check for the behavior-based VIGIL detection rules."""
from __future__ import annotations
import json
import os
import sys

import seed
from validate_alerts import RULE_IDS

def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    rules = []
    for rule_id in RULE_IDS:
        rule = json.loads(seed.request(
            "GET", f"/api/detection_engine/rules?rule_id={rule_id}", base_url=kibana_url,
            extra_headers={"kbn-xsrf": "vigil-local-prototype"},
        ))
        last = rule.get("execution_summary", {}).get("last_execution", {})
        rules.append({"rule_id": rule_id, "type": rule.get("type"), "enabled": rule.get("enabled"), "status": last.get("status", "not-yet-run"), "message": last.get("message"), "date": last.get("date")})
    print(json.dumps({"rules": rules}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
