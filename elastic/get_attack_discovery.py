#!/usr/bin/env python3
"""Read the status and discoveries for a single VIGIL Attack Discovery generation."""
from __future__ import annotations

import argparse
import json
import os
import sys

import seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("execution_uuid")
    args = parser.parse_args()
    seed.load_local_env()
    response = json.loads(seed.request(
        "GET", f"/api/attack_discovery/generations/{args.execution_uuid}",
        base_url=os.environ.get("KIBANA_URL", ""), extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    ))
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
