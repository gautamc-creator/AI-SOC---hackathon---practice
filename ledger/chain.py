"""Minimal, deterministic hash-chain implementation for the VIGIL evidence ledger."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

GENESIS_HASH = "0" * 64


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def append_block(chain: list[dict], event_type: str, payload: dict, timestamp: str | None = None) -> dict:
    block = {
        "sequence": len(chain),
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event_type": event_type,
        "payload": payload,
        "previous_hash": chain[-1]["hash"] if chain else GENESIS_HASH,
    }
    block["hash"] = digest(block)
    chain.append(block)
    return block


def validate_block(block: dict, expected_sequence: int, expected_previous: str) -> str | None:
    if block.get("sequence") != expected_sequence:
        return f"sequence expected {expected_sequence}, got {block.get('sequence')}"
    if block.get("previous_hash") != expected_previous:
        return "previous_hash does not match the preceding block"
    supplied_hash = block.get("hash")
    unsigned = {key: value for key, value in block.items() if key != "hash"}
    if supplied_hash != digest(unsigned):
        return "hash does not match block contents"
    return None
