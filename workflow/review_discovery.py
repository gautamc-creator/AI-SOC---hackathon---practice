#!/usr/bin/env python3
"""Flag unsupported certainty in an AI-generated Attack Discovery narrative.

This is deliberately a small, deterministic guardrail. It does not decide whether
an incident occurred; it tells the analyst where the generated narrative needs
stronger evidence or softer wording.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"

RISKY_CLAIMS = {
    "confirmed": "The alerts correlate suspicious behavior but do not adjudicate compromise or fraud.",
    "confirming": "Correlation is not confirmation; retain this only as an investigation lead.",
    "fraudulent": "No customer dispute, fraud adjudication, or transaction-reversal evidence is present.",
    "attacker": "The actor identity and intent are not established by the available alerts.",
    "successfully authenticated": "A successful login is observed, but attribution to an attacker is not established.",
}


def main() -> None:
    source = ARTIFACTS / "attack-discovery-baseline.json"
    output = ARTIFACTS / "attack-discovery-claim-review.json"
    if not source.exists():
        review = {
            "status": "NOT_RUN",
            "method": "Deterministic phrase-level claim-safety check; not an incident verdict.",
            "reason": "No captured Attack Discovery artifact was available.",
            "submission_effect": "None; human review is still required.",
        }
        output.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
        print("No Attack Discovery capture found; wrote a NOT_RUN claim review.")
        return

    payload = json.loads(source.read_text(encoding="utf-8"))
    discoveries = payload.get("response", {}).get("data", [])
    combined = "\n".join(
        str(discovery.get(field, ""))
        for discovery in discoveries
        for field in ("title", "summary_markdown", "details_markdown", "entity_summary_markdown")
    )
    findings = []
    for phrase, boundary in RISKY_CLAIMS.items():
        if re.search(rf"\b{re.escape(phrase)}\b", combined, flags=re.IGNORECASE):
            findings.append({"phrase": phrase, "review_note": boundary})

    review = {
        "status": "REVIEW_REQUIRED" if findings else "NO_FLAGGED_CERTAINTY_LANGUAGE",
        "method": "Deterministic phrase-level claim-safety check; not an incident verdict or semantic fact checker.",
        "source": "Elastic Security Attack Discovery captured rehearsal output",
        "discovery_count": len(discoveries),
        "alert_context_count": payload.get("response", {}).get("generation", {}).get("alerts_context_count"),
        "findings": findings,
        "safe_interpretation": "Treat the generated narrative as a potential investigation lead. A human must validate compromise, fraud, impact, and reportability.",
        "submission_effect": "None. VIGIL does not contain a system or submit a report based on this check.",
    }
    output.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(f"Attack Discovery claim review: {review['status']} ({len(findings)} phrase(s) flagged).")


if __name__ == "__main__":
    main()
