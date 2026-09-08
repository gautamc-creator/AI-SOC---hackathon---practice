#!/usr/bin/env python3
"""Map the sealed evidence events to MITRE ATT&CK, keeping the two sources separate.

Attack Discovery names tactics in its own narrative. VIGIL maps techniques from the
event tags in the corpus. These are different provenances and the artifact keeps them
distinct so the War Room can label each honestly, rather than presenting a technique
as something the AI concluded.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "mitre-mapping.json"

# The 14 Enterprise tactics, in ATT&CK order, so the matrix shows what was NOT seen too.
ENTERPRISE_TACTICS = [
    ("TA0043", "Reconnaissance"), ("TA0042", "Resource Development"),
    ("TA0001", "Initial Access"), ("TA0002", "Execution"),
    ("TA0003", "Persistence"), ("TA0004", "Privilege Escalation"),
    ("TA0005", "Defense Evasion"), ("TA0006", "Credential Access"),
    ("TA0007", "Discovery"), ("TA0008", "Lateral Movement"),
    ("TA0009", "Collection"), ("TA0011", "Command and Control"),
    ("TA0010", "Exfiltration"), ("TA0040", "Impact"),
]

# Corpus tag -> technique. Each entry states the observable that justifies it.
TAG_TO_TECHNIQUE = {
    "credential_access": {
        "tactic_id": "TA0006", "tactic": "Credential Access",
        "technique_id": "T1110", "technique": "Brute Force",
        "observable": "Repeated failed privileged logins from a single external address.",
    },
    "command_and_control": {
        "tactic_id": "TA0011", "tactic": "Command and Control",
        "technique_id": "T1071.001", "technique": "Application Layer Protocol: Web Protocols",
        "observable": "Outbound TLS session to an unapproved destination immediately after login.",
    },
    "impact": {
        "tactic_id": "TA0040", "tactic": "Impact",
        "technique_id": "T1657", "technique": "Financial Theft",
        "observable": "UPI transfers approved outside the normal payment-service batch profile.",
    },
}


def main() -> None:
    envelope = json.loads((ARTIFACTS / "evidence-envelope.json").read_text(encoding="utf-8"))
    report = json.loads((ARTIFACTS / "incident-report-draft.json").read_text(encoding="utf-8"))
    evidence_ids = set(envelope["evidence_event_ids"])

    observed: dict[str, dict] = {}
    for line in (ARTIFACTS / "events.ndjson").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("_id") not in evidence_ids:
            continue
        for tag in row.get("tags", []):
            mapping = TAG_TO_TECHNIQUE.get(tag)
            if not mapping:
                continue
            entry = observed.setdefault(mapping["technique_id"], {**mapping, "evidence_event_ids": []})
            entry["evidence_event_ids"].append(row["_id"])

    # A successful privileged login after a brute-force run is a distinct technique, and it is
    # read from the event action rather than a tag so the justification stays observable.
    if "hero-login-success" in evidence_ids:
        observed["T1078"] = {
            "tactic_id": "TA0001", "tactic": "Initial Access",
            "technique_id": "T1078", "technique": "Valid Accounts",
            "observable": "Privileged login succeeded from a previously unseen external address.",
            "evidence_event_ids": ["hero-login-success"],
        }

    discovery_tactics = report.get("attack_discovery", {}).get("mitre_attack_tactics", [])
    vigil_tactics = sorted({entry["tactic"] for entry in observed.values()})

    payload = {
        "status": "MAPPED FROM SEALED EVIDENCE",
        "boundary": (
            "Techniques are mapped deterministically by VIGIL from tags and event actions in the "
            "synthetic corpus. They are not conclusions drawn by the AI and are not a claim that "
            "an adversary was present."
        ),
        "framework": "MITRE ATT&CK Enterprise",
        "tactics_named_by_attack_discovery": discovery_tactics,
        "tactics_mapped_by_vigil_from_evidence": vigil_tactics,
        "tactic_agreement": sorted(set(discovery_tactics) & set(vigil_tactics)),
        "tactics_only_claimed_by_ai": sorted(set(discovery_tactics) - set(vigil_tactics)),
        "enterprise_tactics": [{"id": tid, "name": name} for tid, name in ENTERPRISE_TACTICS],
        "observed_techniques": sorted(observed.values(), key=lambda item: item["tactic_id"]),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Mapped {len(observed)} technique(s) across {len(vigil_tactics)} tactic(s); "
        f"{len(payload['tactics_only_claimed_by_ai'])} tactic(s) claimed by the AI alone."
    )


if __name__ == "__main__":
    main()
