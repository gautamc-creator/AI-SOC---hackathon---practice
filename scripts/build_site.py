#!/usr/bin/env python3
"""Assemble the static site that gets deployed, from generated artifacts only.

The War Room is a single HTML file that fetches JSON. That means it needs no server,
no build step and no runtime: it deploys to any static host on a free tier, and it has
no cold start to stall a demo. This script stages the file plus the artifacts it reads
into ``site/`` and refuses to stage anything that is not part of the safe set.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

# Only these artifacts are published. Anything holding a credential, a live cluster
# address or an uncleared draft stays out by construction rather than by filtering.
PUBLISHABLE = {
    "classification.json", "attack-discovery-claim-review.json", "evidence-envelope.json",
    "incident-report-draft.json", "evidence-ledger.json", "review-decision.json",
    "rbi-daksh-information-pack.json", "cert-in-incident-form-draft.json",
    "stix-2.1-draft.json", "notification-preview.json", "evidence-timeline.json",
    "mitre-mapping.json", "attack-topology.json", "escalation-payloads.json", "exposure-query.json",
    "bedrock-grounded-brief.json", "indic-localisation.json", "manifest.json",
}

# A published file must not carry a secret or a live endpoint, so the staged bytes are
# scanned before they are written. This is a publish-time check, not a substitute for
# keeping secrets out of artifacts in the first place.
#
# The scan looks for secret *values*, not variable names: a NOT_RUN record legitimately
# says "SARVAM_API_KEY is not set", and refusing that would be a false positive that
# trains everyone to bypass the guard.
SECRET_SHAPES = (
    "AKIA", "ASIA",              # AWS access key id prefixes
    "aws4_request",              # a SigV4 credential scope, i.e. a signed request leaked
    ".es.io", ".elastic.cloud",  # live cluster endpoints
    "-----BEGIN",                # any PEM private key
)
MIN_SECRET_LENGTH = 12


def env_secret_values() -> list[str]:
    """Every value currently in .env that is long enough to be a real credential."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return []
    values = []
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        value = line.split("=", 1)[1].strip().strip('"').strip("'")
        if len(value) >= MIN_SECRET_LENGTH and not value.startswith("replace-me"):
            values.append(value)
    return values


def main() -> int:
    source_data = ROOT / "warroom" / "data"
    if not source_data.exists():
        print("Run `make demo` first: warroom/data/ does not exist.", file=sys.stderr)
        return 1

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "data").mkdir(parents=True)

    shutil.copy2(ROOT / "warroom" / "index.html", SITE / "index.html")

    secrets = env_secret_values()
    staged, skipped, rejected = [], [], []
    for path in sorted(source_data.glob("*.json")):
        if path.name not in PUBLISHABLE:
            skipped.append(path.name)
            continue
        text = path.read_text(encoding="utf-8")
        hits = [token for token in SECRET_SHAPES if token in text]
        # Redact the finding itself: report that a .env value leaked, never which one.
        hits += [f"a value from .env ({len(v)} chars)" for v in secrets if v in text]
        if hits:
            rejected.append((path.name, hits))
            continue
        (SITE / "data" / path.name).write_text(text, encoding="utf-8")
        staged.append(path.name)

    if rejected:
        for name, hits in rejected:
            print(f"REFUSED {name}: contains {hits}", file=sys.stderr)
        shutil.rmtree(SITE)
        print("\nNothing was staged. Remove the offending values and rerun.", file=sys.stderr)
        return 1

    # A tiny landing redirect keeps the deployed root working on hosts that serve /.
    (SITE / "404.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/">\n',
        encoding="utf-8",
    )
    (SITE / "build-info.json").write_text(json.dumps({
        "site": "VIGIL SOC Cockpit — pre-event rehearsal",
        "data": "synthetic",
        "staged_artifacts": staged,
        "not_published": skipped,
        "boundary": (
            "Static site. No server, no credential, no live cluster address. Every figure is "
            "read from a published artifact in data/."
        ),
        "publish_checks": (
            f"{len(SECRET_SHAPES)} credential shapes and every value in .env were scanned for "
            "in each staged file before writing."
        ),
    }, indent=2) + "\n", encoding="utf-8")

    total = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    print(f"Staged {len(staged)} artifact(s) into {SITE.relative_to(ROOT)}/ ({total/1024:.0f} KB total).")
    if skipped:
        print(f"Not published ({len(skipped)}): {', '.join(skipped)}")
    print("\nDeploy with either:")
    print("  make deploy-vercel                # Vercel free tier")
    print("  git push origin main              # GitHub Pages via .github/workflows/pages.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
