#!/usr/bin/env python3
"""Copy safe, generated proof artifacts into the offline VIGIL War Room."""
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "warroom" / "data"

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename in ("incident-report-draft.json", "evidence-ledger.json", "review-decision.json", "rbi-daksh-submission-draft.json", "cert-in-notification-draft.json", "stix-2.1-draft.json"):
        source = ROOT / "artifacts" / filename
        if source.exists(): shutil.copy2(source, OUT / filename)
    (OUT / "manifest.json").write_text(json.dumps({"generated_from": "synthetic VIGIL rehearsal artifacts", "files": sorted(p.name for p in OUT.glob("*.json"))}, indent=2) + "\n", encoding="utf-8")
    print("Prepared offline War Room data.")

if __name__ == "__main__": main()
