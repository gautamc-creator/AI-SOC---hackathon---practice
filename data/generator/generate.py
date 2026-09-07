#!/usr/bin/env python3
"""Create a deterministic, synthetic VIGIL demo corpus.

The corpus deliberately contains one reportable hero incident and one suspicious
but benign decoy. It has no customer or production information.
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
SEED = 20260906
HERO_HOST = "pay-svc-prod-01"
DECOY_HOST = "pay-svc-batch-01"


def event(event_id: str, timestamp: datetime, host: str, category: str, action: str,
          outcome: str, message: str, **extra: object) -> dict:
    event_types = {"authentication": ["start"], "network": ["connection"], "web": ["access"]}
    result = {
        "_id": event_id,
        "@timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "event": {
            "kind": "event", "category": [category], "type": event_types[category], "action": action, "outcome": outcome,
            "created": (timestamp + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
        },
        "host": {"name": host},
        "service": {"name": "upi-payment-gateway"},
        "message": message,
        "labels": {"dataset": "vigil-synthetic", "synthetic": "true"},
    }
    result.update(extra)
    source_ip = result.get("source", {}).get("ip")
    if source_ip:
        zone = "external" if source_ip.startswith(("198.51.100.", "203.0.113.")) else "internal"
        result.setdefault("vigil", {}).setdefault("security", {})["source_zone"] = zone
    return result


def write_ndjson(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    start = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)
    events: list[dict] = []
    # Normal operational telemetry across thirty days.
    for day in range(30):
        for n in range(4):
            ts = start + timedelta(days=day, minutes=n * 35 + rng.randint(0, 5))
            host = f"pay-svc-prod-0{1 + (n % 2)}"
            events.append(event(
                f"normal-{day:02d}-{n}", ts, host, "authentication", "service_token_refresh", "success",
                "Payment-service credential refresh completed.",
                user={"name": "svc-payments"}, source={"ip": f"10.42.0.{20 + n}"},
                related={"ip": [f"10.42.0.{20 + n}"], "user": ["svc-payments"], "hosts": [host]},
            ))

    hero_start = datetime(2026, 9, 6, 8, 30, tzinfo=timezone.utc)
    for n in range(5):
        events.append(event(
            f"hero-auth-{n}", hero_start + timedelta(minutes=n), HERO_HOST, "authentication",
            "login", "failure", "Repeated failed privileged login against payment service.",
            user={"name": "svc-payments-admin"}, source={"ip": "198.51.100.42"},
            related={"ip": ["198.51.100.42"], "user": ["svc-payments-admin"], "hosts": [HERO_HOST]},
            tags=["vigil_hero", "credential_access"],
        ))
    events.append(event(
        "hero-login-success", hero_start + timedelta(minutes=6), HERO_HOST, "authentication", "login", "success",
        "Privileged payment-service login succeeded from a previously unseen external address.",
        user={"name": "svc-payments-admin"}, source={"ip": "198.51.100.42"}, tags=["vigil_hero", "credential_access"],
        related={"ip": ["198.51.100.42"], "user": ["svc-payments-admin"], "hosts": [HERO_HOST]},
    ))
    events.append(event(
        "hero-egress", hero_start + timedelta(minutes=8), HERO_HOST, "network", "connection", "success",
        "Outbound TLS session to an unapproved destination immediately after privileged login.",
        destination={"address": "203.0.113.77", "ip": "203.0.113.77", "port": 443}, source={"ip": "10.42.0.11", "port": 51540},
        user={"name": "svc-payments-admin"},
        network={"transport": "tcp", "protocol": "https"}, related={"ip": ["10.42.0.11", "203.0.113.77"], "hosts": [HERO_HOST]},
        tags=["vigil_hero", "command_and_control"],
    ))
    for n, amount in enumerate((175000, 225000, 310000, 190000, 260000), start=1):
        events.append(event(
            f"hero-upi-{n}", hero_start + timedelta(minutes=10 + n), HERO_HOST, "web", "upi_transfer", "success",
            "UPI transfer approved outside the normal payment-service batch profile.",
            user={"name": "svc-payments-admin"}, source={"ip": "10.42.0.11"},
            transaction={"id": f"UPI-HERO-{n:03d}"},
            http={"request": {"method": "POST"}, "response": {"status_code": 200}},
            url={"path": "/payments/upi/transfer"},
            vigil={"transaction": {"amount": amount, "currency": "INR", "channel": "UPI", "profile": "outside_normal_batch"}},
            related={"user": ["svc-payments-admin"], "hosts": [HERO_HOST]},
            tags=["vigil_hero", "impact"],
        ))

    # Deliberately suspicious decoy: failed logins from a documented maintenance source, no impact.
    decoy_start = datetime(2026, 9, 6, 7, 45, tzinfo=timezone.utc)
    for n in range(4):
        events.append(event(
            f"decoy-auth-{n}", decoy_start + timedelta(minutes=n), DECOY_HOST, "authentication", "login", "failure",
            "Scheduled maintenance account failed to authenticate before credential rotation completed.",
            user={"name": "batch-maintenance"}, source={"ip": "10.99.0.15"}, tags=["vigil_decoy"],
            related={"ip": ["10.99.0.15"], "user": ["batch-maintenance"], "hosts": [DECOY_HOST]},
        ))

    context = [
        {"host.name": HERO_HOST, "vigil.bank.service": "UPI payment gateway", "vigil.bank.tier": "Tier 1",
         "vigil.bank.account_count": 5, "vigil.bank.exposure_inr": 1160000, "vigil.bank.owner": "Payments Operations",
         "vigil.bank.approved_maintenance_ip": "10.99.0.15"},
        {"host.name": DECOY_HOST, "vigil.bank.service": "Nightly settlement batch", "vigil.bank.tier": "Tier 2",
         "vigil.bank.account_count": 0, "vigil.bank.exposure_inr": 0, "vigil.bank.owner": "Settlement Operations",
         "vigil.bank.approved_maintenance_ip": "10.99.0.15"},
    ]
    labels = {
        "scenario": "credential_theft_to_bulk_upi",
        "synthetic": True,
        "hero": {"host": HERO_HOST, "event_ids": [row["_id"] for row in events if "vigil_hero" in row.get("tags", [])],
                 "expected_exposure_inr": 1160000, "reportable": True},
        "decoy": {"host": DECOY_HOST, "event_ids": [row["_id"] for row in events if "vigil_decoy" in row.get("tags", [])],
                  "reportable": False},
    }
    write_ndjson(ARTIFACTS / "events.ndjson", events)
    write_ndjson(ARTIFACTS / "bank-context.ndjson", context)
    (ARTIFACTS / "ground-truth.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(events)} synthetic events and {len(context)} bank-context records in {ARTIFACTS}.")


if __name__ == "__main__":
    main()
