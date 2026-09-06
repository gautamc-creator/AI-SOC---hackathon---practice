#!/usr/bin/env python3
"""Prepare a safe notification preview; it deliberately has no delivery integration."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    report = json.loads((ROOT / "artifacts/incident-report-draft.json").read_text())
    preview = {
        "status": "PREVIEW ONLY — NOT SENT",
        "audience": "Authorised SOC escalation channel (placeholder)",
        "subject": f"VIGIL review requested: {report['incident_id']}",
        "body": f"Potential incident on {report['affected_asset']}. Deterministic fixture exposure: ₹{report['deterministic_exposure_inr']:,}. Review is required; no containment or regulatory submission has occurred.",
        "safe_delivery_boundary": "A future webhook/email connector must be configured and approved by the organisation. This rehearsal never transmits the preview.",
    }
    (ROOT / "artifacts/notification-preview.json").write_text(json.dumps(preview, indent=2) + "\n")
    print("Created notification preview; nothing was sent.")

if __name__ == "__main__": main()
