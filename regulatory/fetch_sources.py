#!/usr/bin/env python3
"""Fetch the real regulatory primary sources VIGIL grounds its reporting decision in.

This is the one part of VIGIL that uses real, live, messy data rather than the
synthetic bank corpus. The bank telemetry is invented; the rulebook is not.

Standard library only, matching the rest of this repository. Every fetch records
the URL, the UTC fetch time, the HTTP status, the byte length and a SHA-256 of the
exact bytes retrieved, so any claim VIGIL later makes about an obligation can be
traced to a specific retrieval of a specific document.

Politeness: these are public government publications. This fetches a handful of
pages, once, read-only, with an identifying user agent and a pause between
requests. Do not turn it into a crawler.
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "regulatory" / "cache"
MANIFEST = ROOT / "regulatory" / "SOURCES.json"

USER_AGENT = "VIGIL-hackathon-prototype/0.1 (research; contact via repository)"
PAUSE_SECONDS = 2.0

# Primary sources only. Each entry states why VIGIL needs it, so nothing is
# fetched "just in case" and every document in the corpus has a stated purpose.
SOURCES = [
    {
        "slug": "cert-in-directions-70b",
        "url": "https://www.cert-in.org.in/Directions70B.jsp",
        "publisher": "CERT-In, Ministry of Electronics and Information Technology, Government of India",
        "why": "Establishes the six-hour reporting obligation and the Annexure I list of "
               "reportable incident types. This is the CERT-In clock in the product.",
        "kind": "html",
    },
    {
        "slug": "rbi-2026-cyber-directions",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13643&Mode=0",
        "publisher": "Reserve Bank of India",
        "why": "Commercial Banks Cybersecurity, Technology Risk, Resilience and Assurance "
               "Framework Directions, 2026. Paragraph 182 carries the six-hour RBI DAKSH "
               "reporting obligation from detection. This is the DAKSH clock in the product.",
        "kind": "html",
    },
    {
        "slug": "cert-in-directions-70b-2022",
        "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf",
        "publisher": "CERT-In",
        "why": "The operative Directions themselves, dated 28.04.2022. Carries the six-hour "
               "reporting obligation from noticing and the Annexure I list of reportable "
               "incident types. Directions70B.jsp is only a link hub - this is the rule text.",
        "kind": "pdf",
    },
    {
        "slug": "cert-in-directions-extension-2022",
        "url": "https://www.cert-in.org.in/PDF/CERT-In_directions_extension_MSMEs_and_validation_27.06.2022.pdf",
        "publisher": "CERT-In",
        "why": "Extension of enforcement timelines. Real regulation is amended in place by "
               "later notices; a grounding corpus that ignores amendments is wrong.",
        "kind": "pdf",
    },
    {
        "slug": "cert-in-faq-may-2022",
        "url": "https://www.cert-in.org.in/PDF/FAQs_on_CyberSecurityDirections_May2022.pdf",
        "publisher": "CERT-In",
        "why": "Official interpretation of the Directions, including what 'noticing' means "
               "for the purpose of starting the clock.",
        "kind": "pdf",
    },
    {
        "slug": "cert-in-incident-reporting-form",
        "url": "https://www.cert-in.org.in/PDF/certinirform.pdf",
        "publisher": "CERT-In",
        "why": "The field list our CERT-In-compatible draft mirrors. Guidance, not a "
               "mandatory form - VIGIL must not claim this form is required.",
        "kind": "pdf",
    },
]


def tls_context() -> ssl.SSLContext:
    """Use the macOS CA bundle when this Python build has no default CA path.

    Identical to elastic/seed.py so the whole repository verifies TLS the same way.
    Verification stays enabled. Set VIGIL_CA_BUNDLE only when a company-managed
    certificate bundle is required.
    """
    bundle = Path(os.environ.get("VIGIL_CA_BUNDLE", "/etc/ssl/cert.pem"))
    if bundle.is_file():
        return ssl.create_default_context(cafile=str(bundle))
    return ssl.create_default_context()


def fetch(url: str) -> tuple[bytes, int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response:
        return response.read(), response.status, response.headers.get("Content-Type", "")


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    records = []
    failures = 0

    for index, source in enumerate(SOURCES):
        if index:
            time.sleep(PAUSE_SECONDS)
        print(f"fetching {source['slug']} ... ", end="", flush=True)
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            body, status, content_type = fetch(source["url"])
        except (urllib.error.URLError, TimeoutError) as error:
            failures += 1
            print(f"FAILED ({error})")
            records.append({**source, "fetched_at_utc": fetched_at, "ok": False,
                            "error": str(error)})
            continue

        suffix = ".pdf" if source["kind"] == "pdf" else ".html"
        path = CACHE / f"{source['slug']}{suffix}"
        path.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        print(f"HTTP {status}  {len(body):,}b  sha256 {digest[:16]}...")

        records.append({
            **source,
            "fetched_at_utc": fetched_at,
            "ok": True,
            "http_status": status,
            "content_type": content_type,
            "bytes": len(body),
            "sha256": digest,
            "cached_as": str(path.relative_to(ROOT)),
        })

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Real primary-source regulatory documents retrieved live. The bank telemetry "
                "in this repository is synthetic; these documents are not. Public government "
                "publications, fetched read-only and at low volume for a non-commercial "
                "prototype. Text is quoted for grounding and citation, never republished as "
                "our own, and never presented as legal advice.",
        "user_agent": USER_AGENT,
        "sources": records,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {MANIFEST.relative_to(ROOT)}  ({len(records) - failures}/{len(records)} ok)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
