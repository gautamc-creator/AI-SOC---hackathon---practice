#!/usr/bin/env python3
"""Run one clearly labelled Elastic-managed-LLM Attack Discovery baseline on VIGIL alerts."""
from __future__ import annotations

import json
import os
import sys

import seed

CONNECTOR_ID = "Anthropic-Claude-Sonnet-3-7"
RULE_ID = "vigil-synthetic-payment-compromise-v1"
ALERTS_INDEX = ".alerts-security.alerts-default"


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env before running Attack Discovery.")
    # Reuse the space's approved policy in full. A partial client-side list can
    # accidentally omit required fields (for example `_id`) and fail generation.
    policy = json.loads(seed.request(
        "GET", "/api/security_ai_assistant/anonymization_fields/_find?all_data=true",
        base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    ))
    anonymization_fields = policy.get("all", [])
    id_policy = next((item for item in anonymization_fields if item.get("field") == "_id"), None)
    if not id_policy or not id_policy.get("allowed"):
        raise RuntimeError("Attack Discovery requires _id to be allowed by the current Security AI anonymization policy.")
    body = {
        "alertsIndexPattern": ALERTS_INDEX,
        "anonymizationFields": anonymization_fields,
        "apiConfig": {"actionTypeId": ".gen-ai", "connectorId": CONNECTOR_ID, "provider": "Other"},
        "connectorName": "Anthropic Claude Sonnet 3.7",
        "start": "now-30d",
        "end": "now",
        "size": 20,
        "subAction": "invokeAI",
        "replacements": {},
        "filter": {"bool": {"filter": [{"term": {"kibana.alert.rule.rule_id": RULE_ID}}]}},
    }
    response = json.loads(seed.request(
        "POST", "/api/attack_discovery/_generate", json.dumps(body).encode(),
        base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    ))
    print(json.dumps({
        "label": "Elastic preconfigured-LLM baseline — not an AWS Bedrock demonstration",
        "connector_id": CONNECTOR_ID,
        "execution_uuid": response.get("execution_uuid"),
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
