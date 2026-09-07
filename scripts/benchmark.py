#!/usr/bin/env python3
"""Measure the deterministic local rehearsal path without implying production SLOs."""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks" / "local-rehearsal.json"
STAGES = [
    ("generate_fixture", ["data/generator/generate.py"]),
    ("review_ai_claims", ["workflow/review_discovery.py"]),
    ("classify_fixture", ["workflow/classify.py"]),
    ("gather_evidence", ["workflow/gather_evidence.py"]),
    ("draft_report", ["report/generate.py"]),
    ("record_human_hold", ["approvals/review.py", "--decision", "hold"]),
    ("prepare_compliance", ["compliance/generate.py"]),
    ("prepare_notification", ["notifications/prepare.py"]),
    ("prepare_war_room", ["warroom/prepare.py"]),
    ("verify_ledger", ["ledger/verify.py", "artifacts/evidence-ledger.json"]),
]


def percentile(values: list[float], proportion: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * proportion)))
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    if args.runs < 3:
        raise SystemExit("Use at least three runs for a minimally useful local benchmark.")

    runs = []
    for number in range(1, args.runs + 1):
        stage_times = {}
        started = time.perf_counter_ns()
        for name, command in STAGES:
            stage_started = time.perf_counter_ns()
            result = subprocess.run([sys.executable, *command], cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(f"Benchmark stage {name} failed: {result.stderr or result.stdout}")
            stage_times[name] = round((time.perf_counter_ns() - stage_started) / 1_000_000, 3)
        runs.append({
            "run": number,
            "total_ms": round((time.perf_counter_ns() - started) / 1_000_000, 3),
            "stages_ms": stage_times,
        })

    totals = [run["total_ms"] for run in runs]
    result = {
        "status": "LOCAL REHEARSAL MEASUREMENT — NOT A PRODUCTION SLO",
        "measured_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Deterministic local Python path over 136 synthetic events. Excludes Elasticsearch network time, detection-rule scheduling, Attack Discovery/LLM generation, UI rendering, and regulator systems.",
        "environment": {"platform": platform.platform(), "python": platform.python_version()},
        "runs": runs,
        "summary_ms": {
            "minimum": round(min(totals), 3),
            "median": round(statistics.median(totals), 3),
            "p95_nearest_rank": round(percentile(totals, 0.95), 3),
            "maximum": round(max(totals), 3),
        },
        "fixture_conformance": {
            "events": 136,
            "hero_evidence_events": 12,
            "benign_decoy_events": 4,
            "expected_exposure_inr": 1160000,
            "claim": "Fixture conformance only; not model accuracy, recall, false-positive rate, or production throughput.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_ms"], indent=2))
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
