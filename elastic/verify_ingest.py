#!/usr/bin/env python3
"""Read-only proof that VIGIL's live ingest pipeline enriched every synthetic event."""
from __future__ import annotations
import json
import sys

import seed

def main() -> None:
    seed.load_local_env()
    body = {
        "size": 0,
        "track_total_hits": True,
        "query": {"bool": {"filter": [
            {"term": {"labels.dataset": "vigil-synthetic"}},
            {"term": {"tags": "vigil_rehearsal"}},
            {"term": {"event.kind": "event"}},
        ]}},
    }
    response = json.loads(seed.request("POST", "/logs-vigil-security/_search", json.dumps(body).encode()))
    count = response["hits"]["total"]["value"]
    if count != 136:
        raise RuntimeError(f"Expected 136 enriched synthetic events, found {count}.")
    print(json.dumps({"pipeline": "vigil-normalize", "enriched_event_count": count, "status": "PASS"}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
