#!/usr/bin/env python3
"""Run one controlled full VIGIL workflow rehearsal with no response action."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import create_case
import seed

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 210
TERMINAL = {"completed", "failed", "cancelled", "timed_out"}
WAITING = {"waiting_for_input", "waiting-for-input", "waiting"}


def yaml_value(value: str) -> str:
    """JSON strings are valid YAML scalars and safely preserve generated text."""
    return json.dumps(value, ensure_ascii=False)


def workflow_yaml(discovery: dict, alerts: list[dict]) -> str:
    prompt = """Use only the supplied text; do not call tools. Identify evidence gaps and unsupported certainty. Do not decide that compromise, fraud, impact, or reportability is confirmed. Separate observed statements from inferences.\n\n""" + "\n".join(
        [
            f"Title: {discovery.get('title', '')}",
            f"Summary: {discovery.get('summary_markdown', '')}",
            f"Details: {discovery.get('details_markdown', '')}",
            f"Entities: {discovery.get('entity_summary_markdown', '')}",
            f"Risk score: {discovery.get('risk_score', '')}",
        ]
    )
    description = """Synthetic full-chain rehearsal only. Potential incident; not confirmed compromise or fraud. This workflow executes no containment, notification, or regulator submission.\n\n""" + discovery.get(
        "summary_markdown", ""
    )
    parts = [
        "name: VIGIL controlled full-chain rehearsal",
        "enabled: false",
        "triggers:",
        "  - type: manual",
        "steps:",
        "  - name: create_case",
        "    type: cases.createCase",
        "    with:",
        f"      title: {yaml_value('[VIGIL full-chain rehearsal] Potential payment-service incident')}",
        f"      description: {yaml_value(description)}",
        "      owner: securitySolution",
        "      severity: high",
        "      tags: [VIGIL, synthetic, full-chain-test, human-review-required]",
    ]
    for index, alert in enumerate(alerts, start=1):
        parts.extend(
            [
                f"  - name: attach_alert_{index}",
                "    type: cases.addAlerts",
                "    with:",
                '      case_id: "{{ steps.create_case.output.case.id }}"',
                "      alerts:",
                f"        - alertId: {yaml_value(alert['alert_id'])}",
                f"          index: {yaml_value(alert['index'])}",
                "          rule:",
                f"            id: {yaml_value(alert['rule']['id'] or '')}",
                f"            name: {yaml_value(alert['rule']['name'] or '')}",
            ]
        )
    parts.extend(
        [
            "  - name: identify_evidence_gaps",
            "    type: ai.agent",
            "    agent-id: elastic-ai-agent",
            "    create-conversation: false",
            "    with:",
            f"      message: {yaml_value(prompt)}",
            "  - name: add_agent_review",
            "    type: cases.addComment",
            "    with:",
            '      case_id: "{{ steps.create_case.output.case.id }}"',
            '      comment: "## Agent-proposed evidence gaps — HUMAN REVIEW REQUIRED\\n{{ steps.identify_evidence_gaps.output.message }}\\n\\nNo action or submission has been executed."',
            "  - name: human_decision",
            "    type: waitForInput",
            "    timeout: 5m",
            "    with:",
            "      message: \"Choose approve, hold, or reject. No downstream response action exists in this rehearsal.\"",
            "      schema:",
            "        type: object",
            "        properties:",
            "          decision:",
            "            type: string",
            "            enum: [approve, hold, reject]",
            "          analyst_notes:",
            "            type: string",
            "        required: [decision]",
            "  - name: record_human_decision",
            "    type: cases.addComment",
            "    with:",
            '      case_id: "{{ steps.create_case.output.case.id }}"',
            '      comment: "## Accountable human decision\\nDecision: {{ steps.human_decision.output.response.decision }}\\nNotes: {{ steps.human_decision.output.response.analyst_notes }}\\n\\nNo containment or regulator submission is authorised."',
        ]
    )
    return "\n".join(parts) + "\n"


def get_execution(kibana_url: str, execution_id: str) -> dict:
    return json.loads(
        seed.request(
            "GET",
            f"/api/workflows/executions/{execution_id}?includeOutput=true",
            base_url=kibana_url,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Authorise one synthetic case and one constrained Agent Builder execution.",
    )
    args = parser.parse_args()
    if not args.live:
        raise RuntimeError("Refusing side effects without --live.")

    seed.load_local_env()
    kibana_url = os.environ.get("KIBANA_URL", "").rstrip("/")
    if not kibana_url:
        raise RuntimeError("Set KIBANA_URL in .env.")
    _, discovery, _ = create_case.load_context()
    alerts = create_case.component_alerts(discovery.get("alert_ids", []))
    if len(alerts) != 3:
        raise RuntimeError(f"Expected three component alerts, found {len(alerts)}.")

    headers = {"kbn-xsrf": "vigil-local-prototype"}
    definition = workflow_yaml(discovery, alerts)
    created = json.loads(
        seed.request(
            "POST",
            "/api/workflows/test",
            json.dumps({"workflowYaml": definition, "inputs": {}}).encode(),
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
        time.sleep(5)
    status_before = str(execution.get("status", "")).lower()
    if status_before not in WAITING:
        raise RuntimeError(f"Full workflow did not reach the human gate: {json.dumps(execution, indent=2)}")

    seed.request(
        "POST",
        f"/api/workflows/executions/{execution_id}/resume",
        json.dumps(
            {
                "input": {
                    "decision": "hold",
                    "analyst_notes": "Review raw authentication evidence before any action.",
                }
            }
        ).encode(),
        base_url=kibana_url,
        extra_headers=headers,
    )
    while time.monotonic() - started < TIMEOUT_SECONDS:
        execution = get_execution(kibana_url, execution_id)
        if str(execution.get("status", "")).lower() in TERMINAL:
            break
        time.sleep(3)
    if str(execution.get("status", "")).lower() != "completed":
        raise RuntimeError(f"Full workflow did not complete after hold: {json.dumps(execution, indent=2)}")

    steps = execution.get("stepExecutions", [])
    failed = [step for step in steps if step.get("status") != "completed"]
    if failed:
        raise RuntimeError(f"One or more workflow steps failed: {json.dumps(failed, indent=2)}")
    case_steps = [step for step in steps if step.get("stepId") == "create_case"]
    case_id = case_steps[0].get("output", {}).get("case", {}).get("id") if case_steps else None
    if not case_id:
        raise RuntimeError("The completed workflow did not return a case ID.")
    case = json.loads(seed.request("GET", f"/api/cases/{case_id}", base_url=kibana_url))
    if case.get("title") != "[VIGIL full-chain rehearsal] Potential payment-service incident":
        raise RuntimeError("Created case could not be verified by read-back.")

    agent_steps = [step for step in steps if step.get("stepId") == "identify_evidence_gaps"]
    agent_usage = agent_steps[0].get("output", {}).get("metadata", {}).get("usage", {}) if agent_steps else {}
    proof = {
        "status": "PASS — CONTROLLED FULL VIGIL WORKFLOW",
        "execution_id": execution_id,
        "case_id": case_id,
        "attached_alerts": len(alerts),
        "paused_status": status_before,
        "decision": "hold",
        "step_count": len(steps),
        "duration_ms": execution.get("duration"),
        "agent_usage": agent_usage,
        "scope": "Synthetic rehearsal only; no containment, external notification, or regulator submission step exists.",
    }
    (ROOT / "artifacts/workflow-full-test.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
