#!/usr/bin/env python3
"""Derive the attack topology graph from the sealed evidence events.

The War Room draws this; it does not invent it. Nodes and edges exist only where an
evidence event supports them, and every edge carries the event id that produced it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "attack-topology.json"

EXTERNAL_PREFIXES = ("198.51.100.", "203.0.113.")


def _zone(ip: str) -> str:
    return "external" if ip.startswith(EXTERNAL_PREFIXES) else "internal"


def main() -> None:
    envelope = json.loads((ARTIFACTS / "evidence-envelope.json").read_text(encoding="utf-8"))
    evidence_ids = set(envelope["evidence_event_ids"])

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def node(key: str, kind: str, label: str, zone: str) -> None:
        existing = nodes.setdefault(key, {"id": key, "kind": kind, "label": label, "zone": zone, "event_count": 0})
        existing["event_count"] += 1

    for line in (ARTIFACTS / "events.ndjson").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("_id") not in evidence_ids:
            continue

        source_ip = row.get("source", {}).get("ip")
        dest_ip = row.get("destination", {}).get("ip")
        host = row.get("host", {}).get("name")
        user = row.get("user", {}).get("name")
        action = row["event"]["action"]
        outcome = row["event"]["outcome"]

        if source_ip:
            node(f"ip:{source_ip}", "ip", source_ip, _zone(source_ip))
        if dest_ip:
            node(f"ip:{dest_ip}", "ip", dest_ip, _zone(dest_ip))
        if host:
            node(f"host:{host}", "host", host, "internal")
        if user:
            node(f"user:{user}", "identity", user, "internal")

        # An event links its source to what it acted on: the host, or an external destination.
        if source_ip and dest_ip:
            edges.append({"from": f"ip:{source_ip}", "to": f"ip:{dest_ip}",
                          "action": action, "outcome": outcome, "event_id": row["_id"]})
        elif source_ip and host:
            edges.append({"from": f"ip:{source_ip}", "to": f"host:{host}",
                          "action": action, "outcome": outcome, "event_id": row["_id"]})

        amount = row.get("vigil", {}).get("transaction", {}).get("amount")
        if amount is not None and host and user:
            edges.append({"from": f"host:{host}", "to": f"user:{user}", "action": action,
                          "outcome": outcome, "event_id": row["_id"], "amount_inr": amount,
                          "transaction_id": row.get("transaction", {}).get("id")})

    payload = {
        "status": "DERIVED FROM SEALED EVIDENCE",
        "boundary": (
            "Every node and edge is backed by an evidence event id in the synthetic corpus. "
            "Direction shows the observed flow; it does not assert intent or attribution."
        ),
        "evidence_event_count": len(evidence_ids),
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], item["label"])),
        "edges": edges,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Derived topology: {len(nodes)} node(s), {len(edges)} edge(s) from {len(evidence_ids)} evidence events.")


if __name__ == "__main__":
    main()
