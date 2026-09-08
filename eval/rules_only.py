#!/usr/bin/env python3
"""Local, faithful mirrors of VIGIL's Elastic detection rules.

Each function reproduces the exact behavioral condition of the corresponding
rule in ``elastic/rules/*.json`` (threshold field/value or EQL sequence
shape), evaluated in-process against a scenario's event list. This lets the
comparison harness score a "rules alone" baseline without a live Elastic
call. It is a disclosed simplification: the deployed rule 1 hardcodes
``user.name: "svc-payments-admin"`` rather than a per-principal list, so a
real deployment would need that rule parameterized before rules 1-3 could
fire, unmodified, against a different privileged account. That gap is
itself one of this harness's findings — see docs/EVAL-LIVE-CAPTURE.md.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _ts(event: dict) -> datetime | None:
    """Returns None for a missing/malformed timestamp rather than raising, so one bad event
    is quarantined instead of crashing evaluation for the whole batch. Callers must check for None."""
    raw = event.get("@timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def malformed_timestamp_events(events: list[dict]) -> list[str]:
    return [e.get("_id", "<unknown>") for e in events if _ts(e) is None]


def rule1_privileged_auth_failure_threshold(events: list[dict]) -> dict:
    """Mirrors elastic/rules/01-brute-force-threshold.json (threshold >= 5, grouped by host/user/source.ip)."""
    groups: dict[tuple, int] = {}
    for e in events:
        ev = e.get("event", {})
        if ev.get("category") == ["authentication"] and ev.get("action") == "login" and ev.get("outcome") == "failure" \
                and e.get("user", {}).get("name") and e.get("labels", {}).get("dataset", "").startswith("vigil-synthetic"):
            key = (e["host"]["name"], e["user"]["name"], e.get("source", {}).get("ip"))
            groups[key] = groups.get(key, 0) + 1
    fired = [{"group": key, "count": count} for key, count in groups.items() if count >= 5]
    return {"rule": "privileged_auth_failure_threshold", "fired": bool(fired), "matches": fired}


def rule2_external_login_to_payment_sequence(events: list[dict]) -> dict:
    """Mirrors elastic/rules/02-compromise-sequence-eql.json (external login -> network -> outside-batch UPI, <=20m)."""
    by_host: dict[str, list[dict]] = {}
    for e in events:
        if _ts(e) is None:
            continue  # quarantined: malformed/missing timestamp, cannot participate in a time-ordered sequence
        by_host.setdefault(e["host"]["name"], []).append(e)
    fired = []
    for host, host_events in by_host.items():
        host_events = sorted(host_events, key=_ts)
        logins = [e for e in host_events if e["event"].get("action") == "login" and e["event"].get("outcome") == "success"
                  and e.get("vigil", {}).get("security", {}).get("source_zone") == "external"]
        for login in logins:
            later = [e for e in host_events if _ts(e) > _ts(login)]
            conns = [e for e in later if e["event"].get("category") == ["network"] and e["event"].get("action") == "connection"]
            for conn in conns:
                txns = [e for e in later if _ts(e) > _ts(conn) and e["event"].get("action") == "upi_transfer"
                        and e.get("vigil", {}).get("transaction", {}).get("profile") == "outside_normal_batch"]
                for txn in txns:
                    if (_ts(txn) - _ts(login)).total_seconds() <= 20 * 60:
                        fired.append({"host": host, "login": login["_id"], "connection": conn["_id"], "transaction": txn["_id"]})
    return {"rule": "external_login_to_payment_sequence", "fired": bool(fired), "matches": fired}


def rule3_upi_burst_threshold(events: list[dict]) -> dict:
    """Mirrors elastic/rules/03-upi-burst-threshold.json (threshold >= 5, grouped by host/user, outside_normal_batch)."""
    groups: dict[tuple, int] = {}
    for e in events:
        ev = e.get("event", {})
        if ev.get("category") == ["web"] and ev.get("action") == "upi_transfer" \
                and e.get("vigil", {}).get("transaction", {}).get("profile") == "outside_normal_batch":
            key = (e["host"]["name"], e.get("user", {}).get("name"))
            groups[key] = groups.get(key, 0) + 1
    fired = [{"group": key, "count": count} for key, count in groups.items() if count >= 5]
    return {"rule": "upi_burst_threshold", "fired": bool(fired), "matches": fired}


def rule4_high_aml_risk_upi_burst(events: list[dict]) -> dict:
    """Mirrors rule 04: three high-AML-score UPI events for one host/user."""
    groups: dict[tuple, int] = {}
    for e in events:
        ev = e.get("event", {})
        score = e.get("vigil", {}).get("bank", {}).get("aml_risk_score")
        if ev.get("category") == ["web"] and ev.get("action") == "upi_transfer" \
                and isinstance(score, (int, float)) and score >= 85:
            key = (e["host"]["name"], e.get("user", {}).get("name"))
            groups[key] = groups.get(key, 0) + 1
    fired = [{"group": key, "count": count} for key, count in groups.items() if count >= 3]
    return {"rule": "high_aml_risk_upi_burst", "fired": bool(fired), "matches": fired}


def rule5_kyc_unverified_transfer(events: list[dict]) -> dict:
    """Mirrors rule 05: a UPI transfer carrying an explicit incomplete-KYC flag."""
    matches = [e["_id"] for e in events if e.get("event", {}).get("category") == ["web"]
               and e.get("event", {}).get("action") == "upi_transfer"
               and e.get("vigil", {}).get("bank", {}).get("kyc_verified") is False]
    return {"rule": "kyc_unverified_transfer", "fired": bool(matches), "matches": matches}


def rule6_insider_kyc_tampering(events: list[dict]) -> dict:
    """Mirrors rule 06: five KYC modifications by one user outside their segment."""
    groups: dict[tuple, int] = {}
    for e in events:
        ev = e.get("event", {})
        record = e.get("vigil", {}).get("record", {})
        if ev.get("category") == ["database"] and ev.get("action") == "kyc_record_modified" \
                and record.get("customer_segment") == "unassigned":
            key = (e["host"]["name"], e.get("user", {}).get("name"))
            groups[key] = groups.get(key, 0) + 1
    fired = [{"group": key, "count": count} for key, count in groups.items() if count >= 5]
    return {"rule": "insider_kyc_tampering", "fired": bool(fired), "matches": fired}


def rule7_duplicate_settlement(events: list[dict]) -> dict:
    """Mirrors rule 07: the same settlement transaction id observed at least twice."""
    groups: dict[tuple, int] = {}
    for e in events:
        ev = e.get("event", {})
        profile = e.get("vigil", {}).get("transaction", {}).get("profile")
        transaction_id = e.get("transaction", {}).get("id")
        if ev.get("category") == ["web"] and ev.get("action") == "upi_transfer" \
                and profile == "duplicate_settlement" and transaction_id:
            key = (e["host"]["name"], transaction_id)
            groups[key] = groups.get(key, 0) + 1
    fired = [{"group": key, "count": count} for key, count in groups.items() if count >= 2]
    return {"rule": "duplicate_settlement", "fired": bool(fired), "matches": fired}


def evaluate(events: list[dict]) -> dict:
    rules = (
        rule1_privileged_auth_failure_threshold(events),
        rule2_external_login_to_payment_sequence(events),
        rule3_upi_burst_threshold(events),
        rule4_high_aml_risk_upi_burst(events),
        rule5_kyc_unverified_transfer(events),
        rule6_insider_kyc_tampering(events),
        rule7_duplicate_settlement(events),
    )
    any_fired = any(rule["fired"] for rule in rules)
    final_alert_count = sum(1 for rule in rules if rule["fired"])
    return {
        "rules": {f"rule{index}": rule for index, rule in enumerate(rules, start=1)},
        "any_rule_fired": any_fired,
        "final_alert_count": final_alert_count,
        "naive_escalation_recommended": any_fired,
        "malformed_timestamp_events": malformed_timestamp_events(events),
        "method": "Local predicate mirror of elastic/rules/*.json; no live Elastic call.",
    }
