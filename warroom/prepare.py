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
    # Live sponsor captures are checked-in proof, not deterministic build output.
    # Preserve a previously captured record when CI regenerates the offline golden
    # path without credentials; never preserve a NOT_RUN or malformed record.
    sponsor_names = {"bedrock-grounded-brief.json", "indic-localisation.json"}
    preserved_captures = {}
    for filename in sponsor_names:
        existing = OUT / filename
        if existing.exists():
            try:
                payload = json.loads(existing.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if str(payload.get("status", "")).startswith("CAPTURED"):
                preserved_captures[filename] = payload
    # This directory is generated exclusively by this script. Clear stale artifact
    # names so the War Room never advertises an obsolete report format.
    for stale in OUT.glob("*.json"):
        stale.unlink()
    artifact_names = (
        # core rehearsal proof
        "classification.json", "attack-discovery-claim-review.json", "evidence-envelope.json",
        "incident-report-draft.json", "evidence-ledger.json", "review-decision.json",
        # regulatory drafts
        "rbi-daksh-information-pack.json", "cert-in-incident-form-draft.json",
        "stix-2.1-draft.json", "notification-preview.json",
        # cockpit surfaces
        "evidence-timeline.json", "mitre-mapping.json", "attack-topology.json",
        "escalation-payloads.json", "exposure-query.json",
        # sponsor integrations; present as NOT_RUN records when no credential is set
        "bedrock-grounded-brief.json", "indic-localisation.json",
    )
    for filename in artifact_names:
        source = ROOT / "artifacts" / filename
        if source.exists():
            shutil.copy2(source, OUT / filename)
        elif filename in preserved_captures:
            (OUT / filename).write_text(
                json.dumps(preserved_captures[filename], indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    (OUT / "manifest.json").write_text(json.dumps({"generated_from": "synthetic VIGIL rehearsal artifacts", "files": sorted(p.name for p in OUT.glob("*.json"))}, indent=2) + "\n", encoding="utf-8")
    print("Prepared offline War Room data.")

if __name__ == "__main__": main()
