#!/usr/bin/env python3
"""Index the real regulatory corpus into Elasticsearch with semantic_text (ELSER).

This is deliberately a separate index from the frozen synthetic demo corpus. It
refuses to operate on any index outside the `vigil-regulatory-` prefix so it can
never disturb the rehearsal data or another lane's work.

Standard library only.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "artifacts" / "regulatory-corpus.ndjson"
INDEX = "vigil-regulatory-corpus"
INFERENCE_ID = ".elser-2-elasticsearch"   # verified present on this project

assert INDEX.startswith("vigil-regulatory-"), "guard: refuse to touch non-regulatory indices"


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def tls_context() -> ssl.SSLContext:
    bundle = Path(os.environ.get("VIGIL_CA_BUNDLE", "/etc/ssl/cert.pem"))
    return ssl.create_default_context(cafile=str(bundle)) if bundle.is_file() else ssl.create_default_context()


def request(method: str, path: str, body: bytes | None = None,
            content_type: str = "application/json") -> tuple[int, bytes]:
    url = os.environ["ELASTIC_URL"].rstrip("/") + path
    headers = {"Authorization": f"ApiKey {os.environ['ELASTIC_API_KEY']}"}
    if body is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180, context=tls_context()) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


MAPPING = {
    "mappings": {
        "properties": {
            # semantic_text handles chunking and ELSER inference server-side.
            "text": {"type": "semantic_text", "inference_id": INFERENCE_ID},
            "chunk_id": {"type": "keyword"},
            "source_slug": {"type": "keyword"},
            "source_url": {"type": "keyword"},
            "publisher": {"type": "keyword"},
            "paragraph_number": {"type": "keyword"},
            "retrieved_at_utc": {"type": "date"},
            "source_sha256": {"type": "keyword"},
            "synthetic": {"type": "boolean"},
        }
    }
}


def main() -> int:
    load_env()
    if not os.environ.get("ELASTIC_URL") or not os.environ.get("ELASTIC_API_KEY"):
        print("Set ELASTIC_URL and ELASTIC_API_KEY (see .env.example).", file=sys.stderr)
        return 1
    if not CORPUS.is_file():
        print("Run regulatory/extract.py first.", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"corpus: {len(rows)} citable units")

    request("DELETE", f"/{INDEX}")
    status, body = request("PUT", f"/{INDEX}", json.dumps(MAPPING).encode())
    if status >= 300:
        print(f"create index failed: {status} {body[:400].decode(errors='replace')}", file=sys.stderr)
        return 1
    print(f"created {INDEX} with semantic_text -> {INFERENCE_ID}")

    # Modest batches: each doc triggers ELSER inference server-side.
    sent = 0
    started = time.time()
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        payload = []
        for row in batch:
            payload.append(json.dumps({"index": {"_index": INDEX, "_id": row["chunk_id"]}}))
            payload.append(json.dumps(row, ensure_ascii=False))
        status, body = request("POST", "/_bulk", ("\n".join(payload) + "\n").encode("utf-8"),
                               content_type="application/x-ndjson")
        if status >= 300:
            print(f"bulk failed: {status} {body[:300].decode(errors='replace')}", file=sys.stderr)
            return 1
        result = json.loads(body)
        if result.get("errors"):
            first = next(it["index"] for it in result["items"] if it["index"].get("error"))
            print(f"bulk item error: {json.dumps(first['error'])[:300]}", file=sys.stderr)
            return 1
        sent += len(batch)
        print(f"  indexed {sent}/{len(rows)}")

    request("POST", f"/{INDEX}/_refresh")
    print(f"done in {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
