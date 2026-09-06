#!/usr/bin/env python3
"""Save one actual Attack Discovery response as a demo artifact for report provenance."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("execution_uuid")
    args = parser.parse_args()
    seed.load_local_env()
    response = json.loads(seed.request(
        "GET", f"/api/attack_discovery/generations/{args.execution_uuid}",
        base_url=os.environ.get("KIBANA_URL", ""), extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    ))
    if response.get("generation", {}).get("status") != "succeeded":
        raise RuntimeError(f"Generation is not successful: {response.get('generation', {}).get('status')}")
    output = ROOT / "artifacts/attack-discovery-baseline.json"
    output.write_text(json.dumps({
        "label": "Elastic preconfigured-LLM baseline — not an AWS Bedrock demonstration",
        "source": "Elastic Security Attack Discovery",
        "response": response,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
