#!/usr/bin/env python3
"""Build valid SOC escalation payloads from the real artifacts. Nothing is sent.

Each payload conforms to the target service's documented request schema, so it can
be posted by an authorised operator without reshaping. Every value is read from the
generated artifacts; none is hardcoded. The rehearsal has no delivery credential and
performs no network call, which is why the status field says PREVIEW.

The Elastic connector block is included because a webhook configured inside Elastic
is the supported way to route a detection-rule action, rather than a bespoke poster.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "escalation-payloads.json"


def _load(name: str) -> dict[str, Any]:
    path = ARTIFACTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build() -> dict[str, Any]:
    report = _load("incident-report-draft.json")
    decision = _load("review-decision.json")
    claim_review = report.get("attack_discovery_claim_review", {})
    brief = _load("bedrock-grounded-brief.json")

    incident_id = report["incident_id"]
    exposure = report["deterministic_exposure_inr"]
    asset = report["affected_asset"]
    flagged = len(claim_review.get("findings", []))
    evidence_count = len(report.get("evidence_event_ids", []))

    headline = f"VIGIL review requested: {incident_id}"
    detail = (
        f"Potential credential compromise on {asset} affecting the {report['affected_service']}. "
        f"Deterministic fixture exposure INR {exposure:,}. {evidence_count} evidence events sealed. "
        f"{flagged} AI certainty phrase(s) flagged for human review. "
        f"No containment executed; no regulatory submission made."
    )

    ai_line = "Bedrock grounded brief: not run."
    if brief.get("status") == "CAPTURED":
        verification = brief.get("verification", {})
        provenance = brief.get("provenance", {})
        ai_line = (
            f"Bedrock grounded brief via {provenance.get('model_id', 'unknown model')}: "
            f"{verification.get('status')} "
            f"({verification.get('ungrounded_claim_count', 0)} ungrounded claim(s))."
        )

    slack = {
        "text": headline,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": headline}},
            {"type": "section", "text": {"type": "mrkdwn", "text": detail}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Asset*\n{asset}"},
                {"type": "mrkdwn", "text": f"*Fixture exposure*\nINR {exposure:,}"},
                {"type": "mrkdwn", "text": f"*Analyst decision*\n{decision.get('decision', 'not recorded')}"},
                {"type": "mrkdwn", "text": f"*AI claims flagged*\n{flagged}"},
            ]},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": ai_line}]},
            {"type": "context", "elements": [{"type": "mrkdwn", "text":
                ":warning: Synthetic rehearsal data. Human review required. Nothing filed with RBI or CERT-In."}]},
        ],
    }

    pagerduty = {
        "routing_key": "<PAGERDUTY_ROUTING_KEY — supplied by an authorised operator>",
        "event_action": "trigger",
        "dedup_key": incident_id,
        "payload": {
            "summary": headline,
            "severity": "warning",
            "source": asset,
            "component": report["affected_service"],
            "group": "payments",
            "class": "potential-credential-compromise",
            "timestamp": report["occurrence_start_timestamp_utc"],
            "custom_details": {
                "deterministic_exposure_inr": exposure,
                "evidence_event_count": evidence_count,
                "ai_certainty_phrases_flagged": flagged,
                "analyst_decision": decision.get("decision", "not recorded"),
                "containment_executed": False,
                "regulatory_submission": "none",
                "data": "synthetic rehearsal",
            },
        },
    }

    jira = {
        "fields": {
            "project": {"key": "<JIRA_PROJECT_KEY>"},
            "issuetype": {"name": "Incident"},
            "summary": headline,
            "labels": ["vigil", "synthetic-rehearsal", "human-review-required"],
            "description": (
                f"{detail}\n\n{ai_line}\n\n"
                f"Occurrence start (UTC): {report['occurrence_start_timestamp_utc']}\n"
                f"First observed (UTC): {report['first_observed_timestamp_utc']}\n"
                f"Evidence set hash: {report.get('evidence_envelope', {}).get('evidence_set_hash', 'n/a')}\n\n"
                "This ticket is a rehearsal preview built from synthetic data. It was not created "
                "in any Jira instance."
            ),
        }
    }

    elastic_connector = {
        "purpose": (
            "Route the detection-rule action through Elastic's own connector framework rather "
            "than a bespoke poster, so the escalation is governed by Kibana roles and is visible "
            "in the rule's action history."
        ),
        "connector": {
            "name": "vigil-soc-escalation",
            "connector_type_id": ".webhook",
            "config": {
                "method": "post",
                "url": "<https endpoint supplied by the organisation>",
                "headers": {"content-type": "application/json"},
                "hasAuth": True,
            },
            "secrets": {"user": "<set at configuration time>", "password": "<set at configuration time>"},
        },
        "rule_action_body_template": {
            "incident": "{{context.rule.name}}",
            "alerts": "{{context.alerts.length}}",
            "opened_at": "{{context.date}}",
            "kibana_link": "{{{context.rule.url}}}",
            "boundary": "Human review required. VIGIL executes no containment.",
        },
        "status": "DEFINITION ONLY — not created in the rehearsal deployment",
    }

    return {
        "status": "PREVIEW ONLY — NOT SENT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "incident_id": incident_id,
        "boundary": (
            "These payloads are schema-valid and derived entirely from generated artifacts. "
            "VIGIL holds no delivery credential for Slack, PagerDuty or Jira and makes no network "
            "call. Delivery requires an organisation-approved connector and an authorised operator."
        ),
        "channels": {
            "slack_incoming_webhook": slack,
            "pagerduty_events_v2": pagerduty,
            "jira_rest_issue_create": jira,
            "elastic_webhook_connector": elastic_connector,
        },
    }


def main() -> None:
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(payload['channels'])} escalation payloads; nothing was sent.")
    print(f"written: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
