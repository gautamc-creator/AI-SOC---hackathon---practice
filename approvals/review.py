#!/usr/bin/env python3
"""Record a demonstrative human decision. This never executes containment or sends a report."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", choices=("approve", "hold", "reject"), required=True)
    parser.add_argument("--reviewer", default="demo-analyst")
    args = parser.parse_args()
    report = json.loads((ROOT / "artifacts/incident-report-draft.json").read_text(encoding="utf-8"))
    decision = {"status": "SIMULATED — NO CONTAINMENT EXECUTED", "incident_id": report["incident_id"], "decision": args.decision, "reviewer": args.reviewer, "reviewed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "effect": "A decision audit record only. Any containment and regulator submission remain human-operated actions."}
    (ROOT / "artifacts/review-decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded simulated {args.decision} decision; no containment was executed.")

if __name__ == "__main__":
    main()
