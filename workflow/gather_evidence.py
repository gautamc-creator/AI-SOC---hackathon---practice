#!/usr/bin/env python3
"""Create a reviewable evidence envelope for the one synthetic VIGIL case."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main() -> None:
    events = [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]
    truth = json.loads((ROOT / "artifacts/ground-truth.json").read_text())
    ids = set(truth["hero"]["event_ids"])
    evidence = [event for event in events if event["_id"] in ids]
    envelope = {
        "status": "EVIDENCE ENVELOPE — SYNTHETIC REHEARSAL",
        "case_id": "VIGIL-2026-09-06-001",
        "source": {"data_stream": "logs-vigil-security", "dataset": "vigil-synthetic", "origin": "local deterministic generator"},
        "scope": {"host": truth["hero"]["host"], "event_count": len(evidence), "first_seen_utc": min(e["@timestamp"] for e in evidence), "last_seen_utc": max(e["@timestamp"] for e in evidence)},
        "evidence_event_ids": [event["_id"] for event in evidence],
        "integrity": {"algorithm": "SHA-256", "evidence_set_hash": digest(evidence)},
        "handling_note": "Evidence identifiers and time range are captured for human review. No real customer or bank data is present.",
    }
    (ROOT / "artifacts/evidence-envelope.json").write_text(json.dumps(envelope, indent=2) + "\n")
    print(f"Created evidence envelope for {len(evidence)} events.")

if __name__ == "__main__": main()
