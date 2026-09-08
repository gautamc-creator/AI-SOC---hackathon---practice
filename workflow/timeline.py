#!/usr/bin/env python3
"""Flatten the sealed evidence events into a display timeline for the War Room.

The interface renders this file directly. Building it here rather than in the browser
keeps one rule in force: every row the cockpit shows exists as a generated artifact a
judge can open, so nothing on screen is assembled by the page itself.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "evidence-timeline.json"


def main() -> None:
    envelope = json.loads((ARTIFACTS / "evidence-envelope.json").read_text(encoding="utf-8"))
    order = {event_id: index for index, event_id in enumerate(envelope["evidence_event_ids"])}

    rows = []
    for line in (ARTIFACTS / "events.ndjson").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("_id") not in order:
            continue
        bank = event.get("vigil", {}).get("bank", {})
        transaction = event.get("vigil", {}).get("transaction", {})
        rows.append({
            "id": event["_id"],
            "timestamp": event["@timestamp"],
            "category": event["event"]["category"][0],
            "action": event["event"]["action"],
            "outcome": event["event"]["outcome"],
            "message": event["message"],
            "host": event.get("host", {}).get("name"),
            "user": event.get("user", {}).get("name"),
            "source_ip": event.get("source", {}).get("ip"),
            "destination_ip": event.get("destination", {}).get("ip"),
            "transaction_id": event.get("transaction", {}).get("id"),
            "amount_inr": transaction.get("amount"),
            "account_id": bank.get("account_id"),
            "upi_vpa": bank.get("upi_vpa"),
            "customer_tier": bank.get("customer_tier"),
            "kyc_verified": bank.get("kyc_verified"),
            "aml_risk_score": bank.get("aml_risk_score"),
        })

    rows.sort(key=lambda row: (row["timestamp"], order[row["id"]]))
    payload = {
        "status": "DERIVED FROM SEALED EVIDENCE",
        "boundary": (
            "Rows are the events named in the evidence envelope, nothing more. Amounts, AML scores "
            "and KYC flags are synthetic upstream context, not production bank records."
        ),
        "evidence_event_count": len(rows),
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Flattened {len(rows)} sealed evidence events into {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
