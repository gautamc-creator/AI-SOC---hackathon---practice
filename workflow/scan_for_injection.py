#!/usr/bin/env python3
"""Scan raw event messages for prompt-injection markers before any LLM/agent ever sees them.

This is a deterministic pre-ingestion guardrail, in the same spirit as
``workflow/review_discovery.py`` (which checks an LLM's OUTPUT for
unsupported certainty). This one checks the INPUT: does a log message
attempt to instruct whatever model later summarizes it? It never blocks
ingestion and never changes classification, exposure, or escalation — those
stay deterministic and are computed from structured fields, not message
text. It only raises a visible flag for human review.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INJECTION_MARKERS = [
    "ignore previous instructions", "ignore all prior", "ignore prior", "system override",
    "disregard prior", "disregard previous", "you are now", "reclassify as benign",
    "do not escalate", "set exposure_inr", "override classification", "new instructions:",
]


def scan(events: list[dict]) -> list[dict]:
    findings = []
    for event in events:
        message = str(event.get("message", ""))
        hits = [marker for marker in INJECTION_MARKERS if marker in message.lower()]
        if hits:
            findings.append({"event_id": event.get("_id"), "markers": hits, "message_preview": message[:160]})
    return findings


def main() -> None:
    events_path = ROOT / "artifacts/events.ndjson"
    if not events_path.exists():
        print("No artifacts/events.ndjson found; run `make seed` or the eval harness first.")
        raise SystemExit(1)
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    findings = scan(events)
    result = {
        "status": "REVIEW_REQUIRED" if findings else "NO_INJECTION_MARKERS_FOUND",
        "method": "Deterministic substring scan over raw event message text; not a semantic classifier.",
        "event_count": len(events),
        "flagged_count": len(findings),
        "findings": findings,
        "safety_boundary": "This scan does not alter classification, exposure, or escalation. Those fields are "
                            "computed from structured event fields only and are never derived from message text.",
    }
    (ROOT / "artifacts/injection-scan-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Injection scan: {result['status']} ({len(findings)}/{len(events)} events flagged).")


if __name__ == "__main__":
    main()
