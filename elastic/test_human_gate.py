#!/usr/bin/env python3
"""Prove Elastic's resumable human gate with VIGIL's three-way decision schema."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 60
TERMINAL = {"completed", "failed", "cancelled", "timed_out"}
WAITING = {"waiting_for_input", "waiting-for-input", "waiting"}
HARNESS = """name: VIGIL controlled human-gate harness
enabled: false
triggers:
  - type: manual
steps:
  - name: human_decision
    type: waitForInput
    timeout: 5m
    with:
      message: |
        Choose approve, hold, or reject after reviewing the evidence.
        This controlled test authorises no action.
      schema:
        type: object
        properties:
          decision:
            type: string
            title: Analyst decision
            enum: [approve, hold, reject]
          analyst_notes:
            type: string
            title: Analyst notes
        required: [decision]
  - name: record_decision
    type: console
    with:
      message: "Recorded controlled decision: {{ steps.human_decision.output.response.decision }}"
"""


def get_execution(kibana_url: str, execution_id: str) -> dict:
    return json.loads(
        seed.request(
            "GET",
            f"/api/workflows/executions/{execution_id}?includeOutput=true",
            base_url=kibana_url,
        )
    )


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    headers = {"kbn-xsrf": "vigil-local-prototype"}
    created = json.loads(
        seed.request(
            "POST",
            "/api/workflows/test",
            json.dumps({"workflowYaml": HARNESS, "inputs": {}}).encode(),
            base_url=kibana_url,
            extra_headers=headers,
        )
    )
    execution_id = created["workflowExecutionId"]
    started = time.monotonic()
    execution = {}
    while time.monotonic() - started < TIMEOUT_SECONDS:
        execution = get_execution(kibana_url, execution_id)
        status = str(execution.get("status", "")).lower()
        if status in WAITING or status in TERMINAL:
            break
        time.sleep(2)
    status_before = str(execution.get("status", "")).lower()
    if status_before not in WAITING:
        raise RuntimeError(f"Human gate did not pause for input: {json.dumps(execution, indent=2)}")

    decision = {
        "input": {
            "decision": "hold",
            "analyst_notes": "Controlled rehearsal: investigate raw evidence; execute no action.",
        }
    }
    seed.request(
        "POST",
        f"/api/workflows/executions/{execution_id}/resume",
        json.dumps(decision).encode(),
        base_url=kibana_url,
        extra_headers=headers,
    )
    while time.monotonic() - started < TIMEOUT_SECONDS:
        execution = get_execution(kibana_url, execution_id)
        if str(execution.get("status", "")).lower() in TERMINAL:
            break
        time.sleep(2)
    if str(execution.get("status", "")).lower() != "completed":
        raise RuntimeError(f"Human gate did not complete after resume: {json.dumps(execution, indent=2)}")

    steps = execution.get("stepExecutions", [])
    decision_steps = [step for step in steps if step.get("stepId") == "human_decision"]
    output = decision_steps[0].get("output", {}) if decision_steps else {}
    response = output.get("response", output)
    if response.get("decision") != "hold":
        raise RuntimeError(f"Recorded decision was not hold: {json.dumps(output, indent=2)}")
    proof = {
        "status": "PASS — RESUMABLE NATIVE HUMAN DECISION GATE",
        "execution_id": execution_id,
        "paused_status": status_before,
        "final_status": execution.get("status"),
        "decision": response.get("decision"),
        "scope": "Controlled manual harness using the same waitForInput schema as VIGIL; no case mutation, containment, notification, or submission.",
    }
    (ROOT / "artifacts/workflow-human-gate-test.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
