#!/usr/bin/env python3
"""Render the exposure ES|QL from the sealed incident scope, never fixture literals."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "elastic" / "esql" / "exposure_lookup_join.esql"
OUTPUT = ROOT / "artifacts" / "exposure-query.json"


def esql_string(value: str) -> str:
    """Return a JSON-compatible quoted string, which is also a safe ES|QL string literal."""
    return json.dumps(value, ensure_ascii=True)


def render(scope: dict) -> str:
    required = {"host", "user", "first_seen_utc", "last_seen_utc"}
    missing = sorted(key for key in required if not scope.get(key))
    if missing:
        raise ValueError(f"Cannot render incident query; missing scope field(s): {', '.join(missing)}")
    query = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{host_name}}": esql_string(scope["host"]),
        "{{user_name}}": esql_string(scope["user"]),
        "{{start_utc}}": esql_string(scope["first_seen_utc"]),
        "{{end_utc}}": esql_string(scope["last_seen_utc"]),
    }
    for token, value in replacements.items():
        query = query.replace(token, value)
    unresolved = [token for token in replacements if token in query]
    if unresolved:
        raise ValueError(f"Unresolved ES|QL template tokens: {unresolved}")
    return "\n".join(line for line in query.splitlines() if not line.lstrip().startswith("//"))


def build() -> dict:
    envelope = json.loads((ROOT / "artifacts" / "evidence-envelope.json").read_text(encoding="utf-8"))
    scope = envelope["scope"]
    return {
        "status": "RENDERED_FROM_SEALED_INCIDENT_SCOPE",
        "template": "elastic/esql/exposure_lookup_join.esql",
        "parameters": {key: scope[key] for key in ("host", "user", "first_seen_utc", "last_seen_utc")},
        "query": render(scope),
        "boundary": "The query is incident-scoped from the evidence envelope; it contains no hidden ground-truth tag or fixed IOC.",
    }


def main() -> None:
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered incident-scoped ES|QL for {payload['parameters']['host']} / {payload['parameters']['user']}.")


if __name__ == "__main__":
    main()
