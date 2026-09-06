#!/usr/bin/env python3
"""Classify the fixed rehearsal scenario without claiming an LLM verdict."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def rows() -> list[dict]:
    return [json.loads(line) for line in (ROOT / "artifacts/events.ndjson").read_text().splitlines() if line]

def main() -> None:
    events = rows()
    hero = [event for event in events if "vigil_hero" in event.get("tags", [])]
    actions = {event.get("event", {}).get("action") for event in hero}
    classification = {
        "status": "PRELIMINARY — HUMAN REVIEW REQUIRED",
        "method": "Deterministic rehearsal classifier: tagged evidence pattern, not an LLM or production detection model.",
        "classification": "Potential credential compromise with anomalous UPI transfers",
        "reason_codes": sorted(actions),
        "evidence_event_count": len(hero),
        "confidence": "not_scored",
        "safety_boundary": "This classification is an investigation priority, not confirmation of compromise, fraud, or reportability.",
    }
    (ROOT / "artifacts/classification.json").write_text(json.dumps(classification, indent=2) + "\n")
    print(f"Classified {len(hero)} evidence events as a preliminary investigation lead.")

if __name__ == "__main__": main()
