#!/usr/bin/env python3
"""Generate an analyst brief with a real LLM, then verify every claim it makes.

Why this exists
---------------
An LLM that writes a rupee figure into a regulatory draft is a liability, not a
feature. This step therefore does two things that are normally left out:

1. It builds the prompt from a **closed fact set** derived only from the evidence
   event ids already sealed in the evidence envelope. Nothing else is in scope.
2. It **verifies the generated text against that fact set** before the text is
   allowed anywhere near a compliance artifact. Every financial magnitude
   (any number >= 1000), every IPv4 literal, and every transaction id in the output
   must appear in the evidence. Anything else is reported as ungrounded.

Modes
-----
``--mode grounded``    the constrained prompt used in the demo.
``--mode adversarial`` a deliberately loose prompt that invites speculation, used to
                       prove the verifier actually fires rather than always passing.
``--offline``          re-run the verifier over the last captured output without
                       calling Bedrock, so ``make demo`` stays deterministic and free.

The verifier is a grounding check on magnitudes and identifiers. It is not a
semantic fact checker and does not adjudicate whether an incident occurred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow.review_discovery import RISKY_CLAIMS

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "bedrock-grounded-brief.json"

# Any number at or above this value is treated as a financial or identifier magnitude
# and must be traceable to the evidence. Smaller integers (counts, ordinals, ports)
# are excluded to keep the check precise and explainable.
MAGNITUDE_FLOOR = 1000

IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
NUMBER = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
# Indian magnitude words carry the decimal point, so "3.5 crore" is a 35,000,000 claim
# even though the digits alone fall below MAGNITUDE_FLOOR. These are checked separately.
SCALED = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)\b", re.IGNORECASE)
SCALE_FACTORS = {"lakh": 100000, "lakhs": 100000, "lac": 100000, "lacs": 100000,
                 "crore": 10000000, "crores": 10000000, "cr": 10000000}

SYSTEM_GROUNDED = (
    "You are a Tier-1 SOC analyst assistant for an Indian bank. You write only from the "
    "FACTS block supplied to you. You must not introduce any host, user, IP address, "
    "transaction id, amount, or count that is not present in FACTS. You must not state "
    "that compromise, fraud, or data loss is confirmed; correlated telemetry is an "
    "investigation lead, not an adjudication. If a fact is unknown, write 'not observed'."
)

SYSTEM_ADVERSARIAL = (
    "You are a confident threat-intelligence analyst. Write a decisive incident "
    "narrative. Estimate the likely total financial loss and the number of customer "
    "accounts affected even when the telemetry does not state them, and name the most "
    "probable threat actor infrastructure."
)


def load_fact_set() -> dict[str, Any]:
    """Derive the closed fact set from the sealed evidence ids only."""
    envelope = json.loads((ARTIFACTS / "evidence-envelope.json").read_text(encoding="utf-8"))
    report = json.loads((ARTIFACTS / "incident-report-draft.json").read_text(encoding="utf-8"))
    evidence_ids = set(envelope["evidence_event_ids"])

    events = []
    for line in (ARTIFACTS / "events.ndjson").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("_id") in evidence_ids:
            events.append(row)

    hosts, users, ips, txns, amounts = set(), set(), set(), set(), []
    accounts, unverified_kyc, aml_scores, tiers = set(), set(), [], set()
    timeline = []
    for row in events:
        if host := row.get("host", {}).get("name"):
            hosts.add(host)
        if user := row.get("user", {}).get("name"):
            users.add(user)
        for candidate in (row.get("source", {}).get("ip"), row.get("destination", {}).get("ip")):
            if candidate:
                ips.add(candidate)
        if txn := row.get("transaction", {}).get("id"):
            txns.add(txn)
        amount = row.get("vigil", {}).get("transaction", {}).get("amount")
        if amount is not None:
            amounts.append(amount)
        bank = row.get("vigil", {}).get("bank", {})
        if account := bank.get("account_id"):
            accounts.add(account)
            if bank.get("kyc_verified") is False:
                unverified_kyc.add(account)
        if (score := bank.get("aml_risk_score")) is not None:
            aml_scores.append(score)
        if tier := bank.get("customer_tier"):
            tiers.add(tier)
        timeline.append({
            "id": row["_id"],
            "timestamp": row["@timestamp"],
            "action": row["event"]["action"],
            "outcome": row["event"]["outcome"],
            "message": row["message"],
        })

    return {
        "incident_id": report["incident_id"],
        "hosts": sorted(hosts),
        "users": sorted(users),
        "ip_addresses": sorted(ips),
        "transaction_ids": sorted(txns),
        "individual_transfer_amounts_inr": amounts,
        "observed_transfer_total_inr": sum(amounts),
        "deterministic_exposure_inr": report["deterministic_exposure_inr"],
        # Counted from the evidence, not asserted. The field-provenance audit flagged this
        # as one of the hardcoded constants that would not generalise past the hero scenario.
        "affected_account_count": len(accounts),
        "affected_accounts": sorted(accounts),
        "customer_tiers_affected": sorted(tiers),
        "accounts_without_completed_kyc": sorted(unverified_kyc),
        "max_aml_risk_score": max(aml_scores) if aml_scores else None,
        "evidence_event_count": len(events),
        "window_start_utc": envelope["scope"]["first_seen_utc"],
        "window_end_utc": envelope["scope"]["last_seen_utc"],
        "affected_service": report["affected_service"],
        "timeline": timeline,
        "not_observed": [
            "customer dispute or chargeback records",
            "fraud adjudication outcome",
            "threat-actor attribution",
            "data-exfiltration volume",
        ],
    }


def grounded_values(facts: dict[str, Any]) -> tuple[set[float], set[str], set[str]]:
    """Return the magnitudes, IPv4 literals and identifiers the output may contain."""
    numbers: set[float] = set()
    for amount in facts["individual_transfer_amounts_inr"]:
        numbers.add(float(amount))
    for key in (
        "observed_transfer_total_inr",
        "deterministic_exposure_inr",
        "affected_account_count",
        "evidence_event_count",
    ):
        numbers.add(float(facts[key]))
    # A lakh/crore rendering resolves to the same rupee value, so no extra entries are
    # needed here: verify() multiplies the scale word out before comparing.
    # Years present in the evidence timestamps are legitimate.
    for entry in facts["timeline"]:
        numbers.add(float(entry["timestamp"][:4]))
    return numbers, set(facts["ip_addresses"]), set(facts["transaction_ids"])


def verify(text: str, facts: dict[str, Any]) -> dict[str, Any]:
    """Check the generated text against the closed fact set."""
    allowed_numbers, allowed_ips, allowed_txns = grounded_values(facts)

    checked_numbers, ungrounded_numbers = [], []

    # Pass 1: magnitudes written with an Indian scale word, e.g. "3.5 crore", "11.6 lakh".
    scaled_spans: list[tuple[int, int]] = []
    for match in SCALED.finditer(text):
        scaled_spans.append(match.span())
        digits, word = match.group(1), match.group(2).lower()
        try:
            value = float(digits.replace(",", "")) * SCALE_FACTORS[word]
        except (ValueError, KeyError):
            continue
        written = match.group(0)
        checked_numbers.append(written)
        if value not in allowed_numbers:
            ungrounded_numbers.append({
                "written_as": written,
                "parsed_value": value,
                "reason": "This magnitude does not appear in the sealed evidence set.",
            })

    # Pass 2: bare magnitudes, skipping the digits already consumed by a scale word.
    for match in NUMBER.finditer(text):
        if any(start <= match.start() < end for start, end in scaled_spans):
            continue
        raw = match.group(0)
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        if value < MAGNITUDE_FLOOR:
            continue
        checked_numbers.append(raw)
        if value not in allowed_numbers:
            ungrounded_numbers.append({
                "written_as": raw,
                "parsed_value": value,
                "reason": "This magnitude does not appear in the sealed evidence set.",
            })

    checked_ips = IPV4.findall(text)
    ungrounded_ips = [
        {"written_as": ip, "reason": "This address is not present in the evidence events."}
        for ip in checked_ips if ip not in allowed_ips
    ]

    ungrounded_txns = [
        {"written_as": token, "reason": "This transaction id is not present in the evidence events."}
        for token in re.findall(r"\bUPI-[A-Z0-9-]+\b", text)
        if token not in allowed_txns
    ]

    flagged_phrases = [
        {"phrase": phrase, "review_note": note}
        for phrase, note in RISKY_CLAIMS.items()
        if re.search(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE)
    ]

    ungrounded_total = len(ungrounded_numbers) + len(ungrounded_ips) + len(ungrounded_txns)
    return {
        "status": "UNGROUNDED_CLAIMS_FOUND" if ungrounded_total else "ALL_CHECKED_CLAIMS_GROUNDED",
        "method": (
            f"Deterministic grounding check: every number >= {MAGNITUDE_FLOOR}, every IPv4 literal and "
            "every UPI transaction id in the generated text is matched against the sealed evidence set. "
            "Lakh and crore renderings of a grounded magnitude are accepted as the same claim."
        ),
        "boundary": (
            "This is a grounding check on magnitudes and identifiers, not a semantic fact checker. "
            "It does not decide whether an incident occurred."
        ),
        "magnitudes_checked": checked_numbers,
        "ungrounded_magnitudes": ungrounded_numbers,
        "ip_literals_checked": checked_ips,
        "ungrounded_ip_literals": ungrounded_ips,
        "ungrounded_transaction_ids": ungrounded_txns,
        "flagged_certainty_phrases": flagged_phrases,
        "ungrounded_claim_count": ungrounded_total,
        "gate_effect": (
            "Blocked from every compliance artifact; the analyst sees the raw text and the finding."
            if ungrounded_total
            else "Permitted as a review aid only. It is not a verdict and is not submitted anywhere."
        ),
    }


def build_prompt(facts: dict[str, Any], mode: str) -> str:
    instruction = (
        "Write a Tier-1 SOC handover brief of at most 150 words for the duty officer. "
        "Cover: what was observed, the affected service, the observed rupee magnitude, "
        "what is NOT established, and the single next action for a human analyst."
        if mode == "grounded"
        else "Write a decisive 150-word incident report for the bank's board, including your "
             "best estimate of total financial loss, the number of customer accounts affected, "
             "and the threat actor's infrastructure."
    )
    return (
        f"FACTS (the only permitted source of truth):\n{json.dumps(facts, indent=2)}\n\n"
        f"TASK:\n{instruction}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("grounded", "adversarial"), default="grounded")
    parser.add_argument(
        "--offline", action="store_true",
        help="Re-verify the last captured output without calling Bedrock.",
    )
    args = parser.parse_args()

    facts = load_fact_set()
    prompt = build_prompt(facts, args.mode)
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    if args.offline:
        if not OUTPUT.exists():
            OUTPUT.write_text(json.dumps({
                "status": "NOT_RUN",
                "reason": "No Bedrock output has been captured yet. Run `make brief-live`.",
                "boundary": "The demo does not depend on this step; it is an additive AI layer.",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }, indent=2) + "\n", encoding="utf-8")
            print("No captured Bedrock output; wrote a NOT_RUN brief. `make demo` is unaffected.")
            return 0
        captured = json.loads(OUTPUT.read_text(encoding="utf-8"))
        text = captured.get("model_output", "")
        if not text:
            print(f"Captured brief has no model output (status {captured.get('status')}); nothing to re-verify.")
            return 0
        captured["verification"] = verify(text, facts)
        captured["reverified_at_utc"] = datetime.now(timezone.utc).isoformat()
        OUTPUT.write_text(json.dumps(captured, indent=2) + "\n", encoding="utf-8")
        print(f"Re-verified captured brief offline: {captured['verification']['status']}")
        return 0

    from llm.bedrock import BedrockUnavailable, converse

    system = SYSTEM_GROUNDED if args.mode == "grounded" else SYSTEM_ADVERSARIAL
    try:
        result = converse(prompt, system=system)
    except BedrockUnavailable as error:
        OUTPUT.write_text(json.dumps({
            "status": "NOT_RUN",
            "mode": args.mode,
            "reason": str(error)[:600],
            "boundary": "No AI claim is made when the model cannot be reached. `make demo` is unaffected.",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print(f"Bedrock unavailable; wrote a NOT_RUN brief.\n{error}")
        return 1

    verification = verify(result["text"], facts)
    payload = {
        "status": "CAPTURED",
        "mode": args.mode,
        "purpose": (
            "Constrained analyst brief used in the demo."
            if args.mode == "grounded"
            else "Deliberate adversarial probe. The loose prompt is used to prove the grounding "
                 "verifier fires, and its output is never used in any compliance artifact."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "system_prompt": system,
        "prompt_sha256": prompt_sha256,
        "fact_set_supplied": facts,
        "model_output": result["text"],
        "verification": verification,
        "provenance": result["provenance"],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    prov = result["provenance"]
    print(f"mode          : {args.mode}")
    print(f"model         : {prov['model_id']} ({prov['region']}, Bedrock Converse)")
    print(f"tokens in/out : {prov['input_tokens']}/{prov['output_tokens']}  cost USD {prov['estimated_cost_usd']}")
    print(f"verification  : {verification['status']} ({verification['ungrounded_claim_count']} ungrounded claim(s))")
    for item in verification["ungrounded_magnitudes"] + verification["ungrounded_ip_literals"]:
        print(f"  ungrounded  : {item['written_as']}")
    print(f"written       : {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
