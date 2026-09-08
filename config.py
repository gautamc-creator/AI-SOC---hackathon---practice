#!/usr/bin/env python3
"""Shared, dependency-free settings loader for the VIGIL rehearsal.

Existing scripts each carried their own ``load_local_env``. New modules import this
one instead. It never prints a secret and never invents a default credential.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_local_env() -> None:
    """Populate os.environ from ./.env without adding a dependency or logging secrets."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# --- Elastic (already in use by elastic/*.py) -------------------------------
ELASTIC_URL = os.getenv("ELASTIC_URL", "").strip()
KIBANA_URL = os.getenv("KIBANA_URL", "").strip()
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY", "").strip()

# --- AWS Bedrock -----------------------------------------------------------
# Region default is Mumbai to match the Elastic Cloud region used for the rehearsal.
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1").strip()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "").strip()
# Optional pin. Leave empty to let llm/bedrock.py discover what this account can
# actually call, so the recorded model id is always the one really invoked.
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "").strip()
# Cost guard: the rehearsal brief needs a few hundred tokens, never thousands.
BEDROCK_MAX_OUTPUT_TOKENS = int(os.getenv("BEDROCK_MAX_OUTPUT_TOKENS", "600"))

HAS_AWS_CREDS = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

# --- Sarvam AI -------------------------------------------------------------
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").strip()

HAS_SARVAM_CREDS = bool(SARVAM_API_KEY)


def redacted(value: str) -> str:
    """Render a credential for logs without disclosing it."""
    if not value:
        return "<unset>"
    return f"<set: {len(value)} chars, ends {value[-4:]}>"
