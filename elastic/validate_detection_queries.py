#!/usr/bin/env python3
"""Directly validate the EQL behavior query against live synthetic telemetry."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    seed.load_local_env()
    rule = json.loads((ROOT / "elastic/rules/02-compromise-sequence-eql.json").read_text())
    body = {
        "query": rule["query"],
        "event_category_field": rule["event_category_override"],
        "timestamp_field": rule["timestamp_field"],
        "size": 10,
    }
    result = json.loads(seed.request("POST", "/logs-vigil-security/_eql/search", json.dumps(body).encode()))
    sequences = result.get("hits", {}).get("sequences", [])
    if len(sequences) != 1:
        raise RuntimeError(f"Expected exactly one compromise sequence; found {len(sequences)}.")
    event_ids = [[event.get("_id") for event in sequence.get("events", [])] for sequence in sequences]
    print(json.dumps({"query": "external login → egress → anomalous UPI", "sequence_count": len(sequences), "event_ids": event_ids, "status": "PASS"}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
