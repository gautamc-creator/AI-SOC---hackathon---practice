#!/usr/bin/env python3
"""Validate and save the disabled VIGIL workflow in the rehearsal deployment."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ID = "vigil-human-gated-triage"
WORKFLOW = ROOT / "elastic/workflows/vigil-human-gated-triage.yaml"


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    payload = {
        "workflows": [{"id": WORKFLOW_ID, "yaml": WORKFLOW.read_text(encoding="utf-8")}],
    }
    response = json.loads(seed.request(
        "POST", "/api/workflows?overwrite=true", json.dumps(payload).encode(),
        base_url=kibana_url, extra_headers={"kbn-xsrf": "vigil-local-prototype"},
    ))
    failures = response.get("failures", [])
    if failures:
        raise RuntimeError(f"Workflow validation/save failed: {json.dumps(failures, indent=2)}")
    created = response.get("created", [])
    if len(created) != 1 or created[0].get("valid") is not True:
        raise RuntimeError(f"Elastic saved but did not validate the workflow: {json.dumps(created, indent=2)}")
    proof = {
        "status": "VALIDATED AND SAVED DISABLED — LIVE EXECUTION NOT YET PROVEN",
        "workflow_id": WORKFLOW_ID,
        "valid": created[0]["valid"],
        "name": created[0]["name"],
        "enabled": False,
        "human_gate": True,
    }
    (ROOT / "artifacts/workflow-live-proof.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
