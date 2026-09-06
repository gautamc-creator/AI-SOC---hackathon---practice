#!/usr/bin/env python3
"""Seed the synthetic VIGIL corpus into a live Elasticsearch deployment.

This intentionally uses only Python's standard library. It is safe to rerun:
the two demo indices are deleted and recreated, then filled from artifacts.
Never point it at a production cluster or use real data.
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    """Load the two demo settings from .env without adding a dependency or logging secrets."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def tls_context() -> ssl.SSLContext:
    """Use the macOS CA bundle when this Python build has no default CA path.

    Verification stays enabled. Set VIGIL_CA_BUNDLE only when a company-managed
    certificate bundle is required.
    """
    bundle = Path(os.environ.get("VIGIL_CA_BUNDLE", "/etc/ssl/cert.pem"))
    if bundle.is_file():
        return ssl.create_default_context(cafile=str(bundle))
    return ssl.create_default_context()


def request(method: str, path: str, body: bytes | None = None, content_type: str = "application/json",
            base_url: str | None = None, extra_headers: dict[str, str] | None = None) -> bytes:
    url = (base_url or os.environ.get("ELASTIC_URL", "")).rstrip("/") + path
    api_key = os.environ.get("ELASTIC_API_KEY", "")
    if not url or not api_key:
        raise RuntimeError("Set ELASTIC_URL and ELASTIC_API_KEY first (see .env.example).")
    headers = {"Authorization": f"ApiKey {api_key}"}
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30, context=tls_context()) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if error.code == 404 and method == "DELETE":
            return b""
        raise RuntimeError(f"{method} {path} failed ({error.code}): {detail}") from error


def to_nested(document: dict) -> dict:
    """Turn generator's dotted bank-context keys into Elasticsearch objects."""
    output: dict = {}
    for key, value in document.items():
        target = output
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return output


def bulk(index: str, path: Path, transform=lambda value: value, data_stream: bool = False) -> None:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        document = transform(json.loads(line))
        document_id = document.pop("_id", None)
        action_name = "create" if data_stream else "index"
        action = {action_name: {"_index": index}}
        if document_id:
            action[action_name]["_id"] = document_id
        lines.extend((json.dumps(action), json.dumps(document)))
    pipeline_parameter = "&pipeline=vigil-normalize" if data_stream else ""
    response = json.loads(request("POST", f"/_bulk?refresh=true{pipeline_parameter}", ("\n".join(lines) + "\n").encode(), "application/x-ndjson"))
    if response.get("errors"):
        failures = [item for item in response["items"] if next(iter(item.values())).get("error")]
        raise RuntimeError(f"Bulk indexing failed: {json.dumps(failures[:3], indent=2)}")


def main() -> None:
    load_local_env()
    events = ROOT / "artifacts/events.ndjson"
    context = ROOT / "artifacts/bank-context.ndjson"
    mapping = ROOT / "elastic/mappings/vigil-bank-context.json"
    ingest_pipeline = ROOT / "elastic/ingest/vigil-normalize.json"
    if not events.exists() or not context.exists():
        raise RuntimeError("Run `python3 data/generator/generate.py` before seeding Elastic.")

    request("DELETE", "/_data_stream/logs-vigil-security")
    request("DELETE", "/vigil-bank-context")
    request("PUT", "/_ingest/pipeline/vigil-normalize", ingest_pipeline.read_bytes())
    request("PUT", "/_data_stream/logs-vigil-security")
    request("PUT", "/vigil-bank-context", mapping.read_bytes())
    bulk("logs-vigil-security", events, data_stream=True)
    bulk("vigil-bank-context", context, to_nested)
    print("Seeded logs-vigil-security and vigil-bank-context; installed ingest pipeline vigil-normalize. Run elastic/esql/exposure_lookup_join.esql in Kibana.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
