#!/usr/bin/env python3
"""Create a deterministic, synthetic VIGIL demo corpus.

The corpus deliberately contains one reportable hero incident and one suspicious
but benign decoy. It has no customer or production information.

Bank-domain fields live under ``vigil.bank.*``. ECS reserves the top-level
namespace, so custom fields sit behind a vendor prefix: a future ECS release
cannot then collide with them, and a reader can tell at a glance which fields are
ECS and which are ours. ``vigil.bank.*`` carries the KYC and AML context the
submission promised; ``vigil.transaction.*`` keeps the payment mechanics it
already had.

``--volume`` scales only the benign background. The hero and decoy event ids,
amounts, and account set are fixed literals so the exposure figure, the dashboard
panels and the eval harness stay reproducible at any volume.
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

# The five accounts touched by the hero incident. Fixed so exposure, the affected
# account count and the ES|QL panels are all derived from one place.
HERO_TRANSFERS = [
    # txn, amount_inr, account_id,      upi_vpa,             tier,        kyc,   aml
    (1, 175000, "ACC-CORP-4417", "payroll.apex@upi",  "Corporate", True,  91.2),
    (2, 225000, "ACC-CORP-4418", "vendor.apex@upi",   "Corporate", True,  88.7),
    (3, 310000, "ACC-HNI-7731",  "r.mehta@upi",       "HNI",       True,  94.5),
    (4, 190000, "ACC-RET-2290",  "s.iyer@upi",        "Retail",    False, 89.1),
    (5, 260000, "ACC-HNI-7732",  "k.rao@upi",         "HNI",       True,  92.8),
]
HERO_BATCH_ID = "UPI-BATCH-20260906-0841"
HERO_EXPOSURE_INR = sum(row[1] for row in HERO_TRANSFERS)
HERO_ACCOUNT_COUNT = len({row[2] for row in HERO_TRANSFERS})


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
    parser.add_argument(
        "--volume", type=int, default=2,
        help="Benign settlement transactions per day. Scales the background only; "
             "the hero and decoy stay fixed.",
    )
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

        # Benign scheduled settlement traffic. This is what gives the corpus a real AML and
        # KYC distribution, so a threshold on those fields separates the hero from routine
        # business instead of matching a hardcoded indicator.
        for n in range(args.volume):
            ts = start + timedelta(days=day, hours=2, minutes=n * 3 + rng.randint(0, 2))
            tier = rng.choice(["Retail", "Retail", "Retail", "HNI", "Corporate"])
            amount = rng.choice([1500, 4200, 8800, 12500, 25000, 48000])
            events.append(event(
                f"settle-{day:02d}-{n:03d}", ts, DECOY_HOST, "web", "upi_transfer", "success",
                "Scheduled settlement transfer within the approved batch profile.",
                user={"name": "svc-settlement"}, source={"ip": "10.42.0.30"},
                transaction={"id": f"UPI-SETTLE-{day:02d}{n:03d}"},
                http={"request": {"method": "POST"}, "response": {"status_code": 200}},
                url={"path": "/payments/upi/transfer"},
                vigil={
                    "transaction": {"amount": amount, "currency": "INR", "channel": "UPI",
                                    "profile": "scheduled_batch"},
                    "bank": {
                        "account_id": f"ACC-{tier[:3].upper()}-{1000 + rng.randint(0, 8999)}",
                        "upi_vpa": f"settle{rng.randint(100, 999)}@upi",
                        "customer_tier": tier,
                        "kyc_verified": True,
                        "aml_risk_score": round(rng.uniform(0.4, 8.0), 1),
                        "batch_id": f"SETTLE-{(start + timedelta(days=day)):%Y%m%d}",
                    },
                },
                related={"user": ["svc-settlement"], "hosts": [DECOY_HOST]},
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
    for txn, amount, account_id, vpa, tier, kyc, aml in HERO_TRANSFERS:
        events.append(event(
            f"hero-upi-{txn}", hero_start + timedelta(minutes=10 + txn), HERO_HOST, "web", "upi_transfer", "success",
            "UPI transfer approved outside the normal payment-service batch profile.",
            user={"name": "svc-payments-admin"}, source={"ip": "10.42.0.11"},
            transaction={"id": f"UPI-HERO-{txn:03d}"},
            http={"request": {"method": "POST"}, "response": {"status_code": 200}},
            url={"path": "/payments/upi/transfer"},
            vigil={
                "transaction": {"amount": amount, "currency": "INR", "channel": "UPI",
                                "profile": "outside_normal_batch"},
                "bank": {
                    "account_id": account_id,
                    "upi_vpa": vpa,
                    "customer_tier": tier,
                    "kyc_verified": kyc,
                    "aml_risk_score": aml,
                    "batch_id": HERO_BATCH_ID,
                },
            },
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
         "vigil.bank.account_count": HERO_ACCOUNT_COUNT, "vigil.bank.exposure_inr": HERO_EXPOSURE_INR,
         "vigil.bank.owner": "Payments Operations", "vigil.bank.approved_maintenance_ip": "10.99.0.15",
         "vigil.bank.criticality": "mission_critical", "vigil.bank.regulated_channel": "UPI",
         "vigil.bank.aml_alert_threshold": 85.0, "vigil.bank.kyc_required": True},
        {"host.name": DECOY_HOST, "vigil.bank.service": "Nightly settlement batch", "vigil.bank.tier": "Tier 2",
         "vigil.bank.account_count": 0, "vigil.bank.exposure_inr": 0,
         "vigil.bank.owner": "Settlement Operations", "vigil.bank.approved_maintenance_ip": "10.99.0.15",
         "vigil.bank.criticality": "business_important", "vigil.bank.regulated_channel": "UPI",
         "vigil.bank.aml_alert_threshold": 85.0, "vigil.bank.kyc_required": True},
    ]
    labels = {
        "scenario": "credential_theft_to_bulk_upi",
        "synthetic": True,
        "benign_settlement_per_day": args.volume,
        "hero": {"host": HERO_HOST, "event_ids": [row["_id"] for row in events if "vigil_hero" in row.get("tags", [])],
                 "expected_exposure_inr": HERO_EXPOSURE_INR, "expected_account_count": HERO_ACCOUNT_COUNT,
                 "expected_accounts": sorted({row[2] for row in HERO_TRANSFERS}),
                 "kyc_unverified_accounts": sorted({row[2] for row in HERO_TRANSFERS if not row[5]}),
                 "reportable": True},
        "decoy": {"host": DECOY_HOST, "event_ids": [row["_id"] for row in events if "vigil_decoy" in row.get("tags", [])],
                  "reportable": False},
    }
    write_ndjson(ARTIFACTS / "events.ndjson", events)
    write_ndjson(ARTIFACTS / "bank-context.ndjson", context)
    (ARTIFACTS / "ground-truth.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
    print(
        f"Generated {len(events)} synthetic events "
        f"({args.volume}/day benign settlement) and {len(context)} bank-context records in {ARTIFACTS}."
    )


if __name__ == "__main__":
    main()
