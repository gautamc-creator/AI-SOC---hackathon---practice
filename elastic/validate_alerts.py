#!/usr/bin/env python3
"""Read only the alerts created by VIGIL's behavior-based rehearsal rules."""
from __future__ import annotations

import json
import sys

import seed

RULE_IDS = [
    "vigil-privileged-auth-failure-threshold-v2",
    "vigil-external-login-payment-sequence-v2",
    "vigil-anomalous-upi-burst-v2",
]


def main() -> None:
    seed.load_local_env()
    body = {
        "size": 100,
        "track_total_hits": True,
        "_source": ["@timestamp", "kibana.alert.rule.name", "kibana.alert.building_block_type", "host.name", "event.action", "event.outcome", "tags"],
        "query": {"terms": {"kibana.alert.rule.rule_id": RULE_IDS}},
        "sort": [{"@timestamp": "asc"}],
    }
    response = json.loads(seed.request("POST", "/.alerts-security.alerts-*/_search", json.dumps(body).encode()))
    hits = response["hits"]
    alerts = [hit["_source"] for hit in hits["hits"]]
    final_alerts = [alert for alert in alerts if not alert.get("kibana.alert.building_block_type")]
    building_blocks = [alert for alert in alerts if alert.get("kibana.alert.building_block_type")]
    counts = {rule_id: sum(1 for alert in final_alerts if alert.get("kibana.alert.rule.name") == name) for rule_id, name in {
        "vigil-privileged-auth-failure-threshold-v2": "VIGIL — privileged authentication failure threshold",
        "vigil-external-login-payment-sequence-v2": "VIGIL — external privileged login to payment activity",
        "vigil-anomalous-upi-burst-v2": "VIGIL — anomalous UPI activity burst",
    }.items()}
    print(json.dumps({"rule_ids": RULE_IDS, "alert_records": hits["total"]["value"], "final_alert_count": len(final_alerts), "building_block_count": len(building_blocks), "final_counts_by_rule": counts, "final_alerts": final_alerts}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
