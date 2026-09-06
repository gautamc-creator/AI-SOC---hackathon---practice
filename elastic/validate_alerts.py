#!/usr/bin/env python3
"""Read only the alerts created by VIGIL's synthetic demo detection rule."""
from __future__ import annotations

import json
import sys

import seed

RULE_ID = "vigil-synthetic-payment-compromise-v1"


def main() -> None:
    seed.load_local_env()
    body = {
        "size": 100,
        "track_total_hits": True,
        "_source": ["@timestamp", "kibana.alert.rule.name", "host.name", "event.action", "event.outcome", "tags"],
        "query": {"term": {"kibana.alert.rule.rule_id": RULE_ID}},
        "sort": [{"@timestamp": "asc"}],
    }
    response = json.loads(seed.request("POST", "/.alerts-security.alerts-*/_search", json.dumps(body).encode()))
    hits = response["hits"]
    print(json.dumps({"rule_id": RULE_ID, "alert_count": hits["total"]["value"], "alerts": [hit["_source"] for hit in hits["hits"]]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
