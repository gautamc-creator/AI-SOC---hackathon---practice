#!/usr/bin/env python3
"""One-command local VIGIL proof: fixture generation → draft → valid ledger → failed tamper check."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*parts: str, expected: int = 0) -> None:
    result = subprocess.run([sys.executable, *parts], cwd=ROOT)
    if result.returncode != expected:
        raise SystemExit(f"Command {' '.join(parts)} returned {result.returncode}; expected {expected}.")


def main() -> None:
    run("data/generator/generate.py")
    run("workflow/review_discovery.py")
    run("workflow/classify.py")
    run("workflow/gather_evidence.py")
    run("report/generate.py")
    run("approvals/review.py", "--decision", "hold")
    run("compliance/generate.py")
    run("notifications/prepare.py")
    run("warroom/prepare.py")
    run("ledger/verify.py", "artifacts/evidence-ledger.json")

    source = ROOT / "artifacts/evidence-ledger.json"
    tampered = ROOT / "artifacts/evidence-ledger.tampered.json"
    ledger = json.loads(source.read_text(encoding="utf-8"))
    ledger[1]["payload"]["amount_inr"] = 1
    tampered.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    run("ledger/verify.py", "artifacts/evidence-ledger.tampered.json", expected=1)
    print("GOLDEN PATH PASS: genuine ledger passes; altered ledger is rejected.")


if __name__ == "__main__":
    main()
