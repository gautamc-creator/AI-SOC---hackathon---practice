#!/usr/bin/env python3
"""Run and verify only the workflow's Agent Builder evidence-gap step."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import seed

ROOT = Path(__file__).resolve().parents[1]
EXECUTION_TIMEOUT_SECONDS = 150


def main() -> None:
    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    headers = {"kbn-xsrf": "vigil-local-prototype"}
    capture = json.loads((ROOT / "artifacts/attack-discovery-baseline.json").read_text(encoding="utf-8"))
    discovery = capture["response"]["data"][0]
    attack_discovery = {
        "title_with_replacements": discovery.get("title", ""),
        "summary_markdown_with_replacements": discovery.get("summary_markdown", ""),
        "details_markdown_with_replacements": discovery.get("details_markdown", ""),
        "entity_summary_markdown_with_replacements": discovery.get("entity_summary_markdown", ""),
    }
    workflow_yaml = (ROOT / "elastic/workflows/vigil-human-gated-triage.yaml").read_text(encoding="utf-8")
    request_body = {
        "stepId": "identify_evidence_gaps",
        "workflowId": "vigil-human-gated-triage",
        "workflowYaml": workflow_yaml,
        "contextOverride": {
            "foreach": {"item": {"attack_discovery": attack_discovery, "risk_score": discovery.get("risk_score")}}
        },
    }
    started = time.monotonic()
    created = json.loads(seed.request(
        "POST", "/api/workflows/step/test", json.dumps(request_body).encode(),
        base_url=kibana_url, extra_headers=headers,
    ))
    execution_id = created["workflowExecutionId"]
    execution = {}
    while time.monotonic() - started < EXECUTION_TIMEOUT_SECONDS:
        execution = json.loads(seed.request(
            "GET", f"/api/workflows/executions/{execution_id}?includeOutput=true",
            base_url=kibana_url,
        ))
        if execution.get("status") in {"completed", "failed", "cancelled", "timed_out"}:
            break
        time.sleep(5)
    else:
        seed.request(
            "POST", f"/api/workflows/executions/{execution_id}/cancel",
            base_url=kibana_url, extra_headers=headers,
        )
        raise RuntimeError(f"Agent Builder step exceeded {EXECUTION_TIMEOUT_SECONDS} seconds and was cancelled.")

    steps = execution.get("stepExecutions", [])
    if execution.get("status") != "completed" or len(steps) != 1 or steps[0].get("status") != "completed":
        raise RuntimeError(f"Agent Builder step did not complete: {json.dumps(execution, indent=2)}")
    output = steps[0].get("output", {})
    proof = {
        "status": "PASS — CONTROLLED AGENT BUILDER STEP",
        "execution_id": execution_id,
        "duration_ms": execution.get("duration"),
        "is_test_run": execution.get("isTestRun"),
        "step": steps[0].get("stepId"),
        "message": output.get("message"),
        "usage": output.get("metadata", {}).get("usage", {}),
        "scope": "Synthetic captured discovery; evidence-gap advice only; no case, containment, notification, or report submission executed.",
    }
    (ROOT / "artifacts/workflow-agent-test.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
