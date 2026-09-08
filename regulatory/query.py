#!/usr/bin/env python3
"""Ask the real regulatory corpus a natural-language question and cite the answer.

This is the grounding path in one file: a question in the analyst's words, semantic
retrieval over verbatim regulator text, and an answer that carries its own citation
- document, paragraph number, retrieval time and source hash.

VIGIL never asserts an obligation it cannot cite this way.
"""
from __future__ import annotations

import json, os, ssl, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = "vigil-regulatory-corpus"


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def search(question: str, size: int = 3) -> dict:
    bundle = Path(os.environ.get("VIGIL_CA_BUNDLE", "/etc/ssl/cert.pem"))
    ctx = ssl.create_default_context(cafile=str(bundle)) if bundle.is_file() else ssl.create_default_context()
    body = json.dumps({
        "size": size,
        "query": {"semantic": {"field": "text", "query": question}},
        "_source": ["chunk_id", "publisher", "paragraph_number", "source_url",
                    "retrieved_at_utc", "source_sha256", "text"],
    }).encode()
    req = urllib.request.Request(
        os.environ["ELASTIC_URL"].rstrip("/") + f"/{INDEX}/_search",
        data=body, method="POST",
        headers={"Authorization": f"ApiKey {os.environ['ELASTIC_API_KEY']}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.load(r)


def main() -> int:
    load_env()
    questions = sys.argv[1:] or [
        "How quickly must a bank tell the regulator after it spots a break-in?",
        "What happens if we do not have every detail ready in time?",
    ]
    for question in questions:
        print(f"\n\033[1mQ: {question}\033[0m")
        for hit in search(question)["hits"]["hits"]:
            s = hit["_source"]
            para = f"paragraph {s['paragraph_number']}" if s.get("paragraph_number") else "unnumbered clause"
            text = " ".join(s["text"].split())
            print(f"\n  score {hit['_score']:.2f}  {s['publisher'][:52]}, {para}")
            print(f"  cite  {s['chunk_id']}  retrieved {s['retrieved_at_utc']}  sha256 {s['source_sha256'][:12]}")
            print(f"  text  {text[:300]}{'...' if len(text) > 300 else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
