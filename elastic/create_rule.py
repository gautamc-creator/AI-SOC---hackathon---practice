#!/usr/bin/env python3
"""Create VIGIL's one transparent demo detection rule through the Kibana API."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env to the Kibana endpoint from Connection details.")
    payload = json.loads((ROOT / "elastic/rules/vigil-hero-chain.json").read_text(encoding="utf-8"))
    response = seed.request(
        "POST",
        "/api/detection_engine/rules",
        json.dumps(payload).encode(),
        base_url=kibana_url,
        extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    )
    created = json.loads(response)
    print(json.dumps({"rule_id": created.get("rule_id"), "id": created.get("id"), "enabled": created.get("enabled")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
