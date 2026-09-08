#!/usr/bin/env python3
"""Read-only validation of the seeded VIGIL data and its ES|QL enrichment query."""
from __future__ import annotations

import json
import sys
import seed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    seed.load_local_env()
    count = json.loads(seed.request("GET", "/logs-vigil-security/_count"))
    rendered = ROOT / "artifacts" / "exposure-query.json"
    if not rendered.exists():
        raise RuntimeError("Run `make demo` first to render incident-scoped ES|QL from the evidence envelope.")
    query = json.loads(rendered.read_text(encoding="utf-8"))["query"]
    result = json.loads(seed.request("POST", "/_query", json.dumps({"query": query}).encode()))
    print(json.dumps({"security_event_count": count["count"], "esql_result": result}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
