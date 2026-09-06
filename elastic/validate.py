#!/usr/bin/env python3
"""Read-only validation of the seeded VIGIL data and its ES|QL enrichment query."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]


def esql_source(path: Path) -> str:
    return "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("//"))


def main() -> None:
    seed.load_local_env()
    count = json.loads(seed.request("GET", "/logs-vigil-security/_count"))
    query = esql_source(ROOT / "elastic/esql/exposure_lookup_join.esql")
    result = json.loads(seed.request("POST", "/_query", json.dumps({"query": query}).encode()))
    print(json.dumps({"security_event_count": count["count"], "esql_result": result}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
