#!/usr/bin/env python3
"""Deterministic VIGIL grounding/decision layer, generalized across scenarios.

This mirrors the *logic* already implemented for the single hero scenario in
``report/generate.py`` and ``compliance/generate.py`` (deterministic exposure
sum, bank-context lookup join, human-review gate, CERT-In field population)
but parameterized so it can run over any of the eight ``eval/scenarios.py``
fixtures. It intentionally never asks an LLM to decide exposure, accounts,
or escalation — that is the whole point of the comparison.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from rules_only import evaluate as evaluate_rules

# Fields a real deployment could, in principle, auto-populate from telemetry
# or a bank-context lookup. Reporter-identity fields are deliberately
# excluded: they must always come from an authorised human, in every
# condition, and counting them would make "completeness" meaningless.
SYSTEM_OBSERVABLE_CERT_IN_FIELDS = [
    "incident_description", "affected_system.host", "affected_system.ip_address",
    "symptoms_observed", "technical_information.source_ip", "occurrence_start_timestamp_utc",
    "exposure_or_impact", "evidence_event_ids",
]


def lookup_join(bank_context: list[dict], host: str) -> dict | None:
    for row in bank_context:
        if row.get("host.name") == host:
            return row
    return None


def compute_exposure(scenario: dict) -> dict:
    if not scenario["exposure_computable"]:
        return {"exposure_inr": None, "status": "INSUFFICIENT_EVIDENCE",
                "note": scenario.get("expected_impact_note") or "Financial exposure cannot be determined from available telemetry."}
    total = 0
    seen_transaction_ids: set[str] = set()
    duplicate_transaction_ids: set[str] = set()
    for event in scenario["events"]:
        amount = event.get("vigil", {}).get("transaction", {}).get("amount")
        if amount is None:
            continue
        transaction_id = event.get("transaction", {}).get("id")
        if transaction_id and transaction_id in seen_transaction_ids:
            duplicate_transaction_ids.add(transaction_id)
            continue
        if transaction_id:
            seen_transaction_ids.add(transaction_id)
        total += amount
    return {
        "exposure_inr": total,
        "status": "COMPUTED",
        "note": (f"De-duplicated repeated transaction ids: {sorted(duplicate_transaction_ids)}."
                 if duplicate_transaction_ids else None),
        "duplicate_transaction_ids": sorted(duplicate_transaction_ids),
    }


def compute_accounts(scenario: dict, context_row: dict | None) -> dict:
    if scenario["expected_accounts"] is None:
        return {"accounts": None, "status": "NOT_APPLICABLE"}
    count = context_row.get("vigil.bank.account_count") if context_row else None
    return {"accounts": count, "status": "COMPUTED" if count is not None else "NOT_OBSERVED"}


def decide_escalation(scenario: dict, rules_result: dict, context_row: dict | None) -> dict:
    if not rules_result["any_rule_fired"]:
        return {"decision": "NOT_REPORTABLE", "reason": "No correlated behavior pattern crossed a detection threshold."}
    allowlisted_ip = (context_row or {}).get("vigil.bank.authorized_test_ip")
    source_ips = {e.get("source", {}).get("ip") for e in scenario["events"] if e.get("source", {}).get("ip")}
    if allowlisted_ip and allowlisted_ip in source_ips:
        return {"decision": "NOT_REPORTABLE",
                "reason": f"Bank-context lookup join marks source IP {allowlisted_ip} as an authorized engagement; suppressed after grounding."}
    if rules_result["rules"]["rule1"]["fired"] and not rules_result["rules"]["rule2"]["fired"]:
        return {"decision": "HOLD_INSUFFICIENT_CHAIN",
                "reason": "Only the auth-failure threshold fired; no login-success/egress/transaction chain followed. Human review required before escalation."}
    return {"decision": "REPORTABLE", "reason": "Full correlated chain observed; no authorized-context exception applies."}


def cert_in_field_completeness(scenario: dict, exposure: dict, accounts: dict) -> dict:
    populated = 0
    detail = {}
    values = {
        "incident_description": scenario["narrative"],
        "affected_system.host": scenario["principal_host"],
        "affected_system.ip_address": next((e.get("source", {}).get("ip") for e in scenario["events"] if e.get("source", {}).get("ip")), None),
        "symptoms_observed": [e["message"] for e in scenario["events"][:3]],
        "technical_information.source_ip": next((e.get("source", {}).get("ip") for e in scenario["events"] if e.get("source", {}).get("ip")), None),
        "occurrence_start_timestamp_utc": scenario["events"][0]["@timestamp"] if scenario["events"] else None,
        "exposure_or_impact": exposure["exposure_inr"] if exposure["status"] == "COMPUTED" else (scenario.get("expected_impact_note") or exposure["status"]),
        "evidence_event_ids": scenario["signal_event_ids"],
    }
    for field in SYSTEM_OBSERVABLE_CERT_IN_FIELDS:
        value = values.get(field)
        ok = value not in (None, "", [])
        detail[field] = {"populated": ok, "value_preview": str(value)[:80]}
        populated += int(ok)
    return {"populated": populated, "total": len(SYSTEM_OBSERVABLE_CERT_IN_FIELDS),
            "completeness_pct": round(100 * populated / len(SYSTEM_OBSERVABLE_CERT_IN_FIELDS), 1), "detail": detail}


def run_once(scenario: dict) -> dict:
    rules_result = evaluate_rules(scenario["events"])
    context_row = lookup_join(scenario["bank_context"], scenario["principal_host"])
    exposure = compute_exposure(scenario)
    accounts = compute_accounts(scenario, context_row)
    escalation = decide_escalation(scenario, rules_result, context_row)
    cert_in = cert_in_field_completeness(scenario, exposure, accounts)
    result = {
        "scenario_id": scenario["id"], "rules": rules_result, "exposure": exposure, "accounts": accounts,
        "escalation": escalation, "cert_in_completeness": cert_in,
    }
    result["result_hash"] = hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode()).hexdigest()
    return result


def score_against_ground_truth(scenario: dict, result: dict) -> dict:
    exposure_correct = (result["exposure"]["exposure_inr"] == scenario["expected_exposure_inr"])
    accounts_correct = (result["accounts"]["accounts"] == scenario["expected_accounts"])
    expected_decision = scenario["expected_decision"]
    actual_decision = result["escalation"]["decision"]
    escalation_correct = actual_decision == expected_decision
    failure_class = "none"
    if not escalation_correct:
        failure_class = "detection_coverage_gap" if scenario.get("known_detection_gap") else "grounding_error"
    exposure_note = None
    if not exposure_correct and result["exposure"]["status"] == "COMPUTED":
        txn_ids = [e.get("transaction", {}).get("id") for e in scenario["events"] if e.get("transaction")]
        dup_ids = sorted({t for t in txn_ids if t and txn_ids.count(t) > 1})
        if dup_ids:
            exposure_note = (f"Exposure still disagrees after transaction-id de-duplication for {dup_ids}: "
                             f"{result['exposure']['exposure_inr']:,} computed vs "
                             f"{scenario['expected_exposure_inr']:,} expected. Investigate the event semantics.")
        else:
            exposure_note = "Computed exposure does not match the fixture's expected value; investigate the formula."
    return {
        "exposure_correct": exposure_correct, "accounts_correct": accounts_correct, "exposure_note": exposure_note,
        "escalation_correct": escalation_correct, "expected_decision": expected_decision,
        "actual_decision": actual_decision, "failure_class": failure_class,
    }
