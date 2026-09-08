#!/usr/bin/env python3
"""Localise the VIGIL incident brief into Indian languages via the Sarvam AI API.

What this does differently
--------------------------
A regional brief is only useful if the rupee figure survives the translation. This
module therefore does not stop at calling the API:

* It translates the **actual generated brief for this incident**, so the localised
  text always carries this run's numbers. There is no pre-written paragraph.
* After each translation it **re-checks that the incident's rupee magnitude is still
  present** in the output, in Latin or Devanagari digits. A number lost or altered in
  localisation is reported as a finding, because a regional brief that misstates the
  exposure is worse than no regional brief.
* With no API key it writes an explicit NOT_RUN record. It never emits placeholder
  text that could be mistaken for a real translation.

Sarvam's translate endpoint caps input length, so longer briefs are split on
sentence boundaries and reassembled.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "indic-localisation.json"

# Sarvam's documented per-request input ceiling for the translate model; kept below it.
MAX_CHUNK_CHARS = 900

LANGUAGES: dict[str, str] = {
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "kn-IN": "Kannada",
    "gu-IN": "Gujarati",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "od-IN": "Odia",
}

# Devanagari and other Indic digit ranges, so a transliterated number still verifies.
INDIC_DIGITS = str.maketrans({
    **{chr(0x0966 + i): str(i) for i in range(10)},  # Devanagari
    **{chr(0x09E6 + i): str(i) for i in range(10)},  # Bengali
    **{chr(0x0A66 + i): str(i) for i in range(10)},  # Gurmukhi
    **{chr(0x0AE6 + i): str(i) for i in range(10)},  # Gujarati
    **{chr(0x0B66 + i): str(i) for i in range(10)},  # Odia
    **{chr(0x0BE6 + i): str(i) for i in range(10)},  # Tamil
    **{chr(0x0C66 + i): str(i) for i in range(10)},  # Telugu
    **{chr(0x0CE6 + i): str(i) for i in range(10)},  # Kannada
    **{chr(0x0D66 + i): str(i) for i in range(10)},  # Malayalam
})


class SarvamUnavailable(RuntimeError):
    pass


def _chunk(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    chunks, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(current) + len(sentence) + 1 > MAX_CHUNK_CHARS and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current.strip())
    return chunks


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not config.HAS_SARVAM_CREDS:
        raise SarvamUnavailable("SARVAM_API_KEY is not set; see .env.example.")
    request = urllib.request.Request(
        f"{config.SARVAM_BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("content-type", "application/json")
    request.add_header("api-subscription-key", config.SARVAM_API_KEY)
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile or defaults.capath:
        tls_context = ssl.create_default_context()
    else:
        system_bundle = Path("/etc/ssl/cert.pem")
        tls_context = ssl.create_default_context(
            cafile=str(system_bundle) if system_bundle.exists() else None
        )
    try:
        with urllib.request.urlopen(request, timeout=45, context=tls_context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SarvamUnavailable(f"Sarvam HTTP {error.code}: {body[:300]}") from None
    except urllib.error.URLError as error:
        raise SarvamUnavailable(f"Sarvam unreachable: {error.reason}") from None


def translate(text: str, target_language_code: str) -> dict[str, Any]:
    """Translate one brief, reassembling chunks in order."""
    parts, request_ids = [], []
    for chunk in _chunk(text):
        response = _post("/translate", {
            "input": chunk,
            "source_language_code": "en-IN",
            "target_language_code": target_language_code,
            "speaker_gender": "Male",
            "mode": "formal",
            "enable_preprocessing": False,
        })
        parts.append(response.get("translated_text", ""))
        if rid := response.get("request_id"):
            request_ids.append(rid)
    return {"translated_text": " ".join(p for p in parts if p).strip(), "request_ids": request_ids}


def check_magnitude_survived(translated: str, expected_values: list[int]) -> dict[str, Any]:
    """Confirm the incident's rupee magnitudes are still readable after localisation."""
    normalised = translated.translate(INDIC_DIGITS)
    # Compare complete numeric tokens. Substring matching would dangerously accept
    # 1,160,000 inside 11,600,000 — a tenfold translation error caught in rehearsal.
    numeric_tokens = re.findall(r"(?<![\d.,])\d[\d,]*(?![\d.,])", normalised)
    observed_values = {
        int(token.replace(",", ""))
        for token in numeric_tokens
        if token.replace(",", "").isdigit()
    }
    missing = [value for value in expected_values if value not in observed_values]
    return {
        "status": "MAGNITUDE_PRESERVED" if not missing else "MAGNITUDE_LOST_IN_TRANSLATION",
        "method": (
            "Indic digit forms are normalised to Latin, comma separators are removed, then each "
            "expected rupee magnitude must equal a complete numeric token."
        ),
        "expected_values": expected_values,
        "missing_values": missing,
        "review_note": (
            "The regional brief carries this incident's figure unchanged."
            if not missing
            else "The figure did not survive localisation. Do not circulate this regional brief; "
                 "the English draft remains authoritative."
        ),
    }


def format_indian_integer(value: int) -> str:
    """Format an integer using Indian lakh/crore digit grouping."""
    digits = str(value)
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return f"{','.join(groups)},{tail}"


def source_brief() -> tuple[str, list[int], str]:
    """Prefer the verified Bedrock brief; otherwise use the deterministic draft.

    A brief carrying ungrounded claims is never localised.
    """
    report = json.loads((ARTIFACTS / "incident-report-draft.json").read_text(encoding="utf-8"))
    exposure = report["deterministic_exposure_inr"]

    captured = ARTIFACTS / "bedrock-grounded-brief.json"
    if captured.exists():
        payload = json.loads(captured.read_text(encoding="utf-8"))
        verification = payload.get("verification", {})
        if (
            payload.get("status") == "CAPTURED"
            and payload.get("mode") == "grounded"
            and verification.get("status") == "ALL_CHECKED_CLAIMS_GROUNDED"
        ):
            return payload["model_output"], [exposure], "verified Bedrock grounded brief"

    indian_grouped = format_indian_integer(exposure)
    deterministic = (
        f"Draft for human review. A potential credential compromise was observed on "
        f"{report['affected_asset']}, affecting the {report['affected_service']}. "
        f"Five UPI transfers totalling INR {indian_grouped} rupees were observed outside the normal "
        f"batch profile. Compromise, fraud and customer impact are not established. "
        f"A human analyst must validate the evidence before any containment or regulatory filing."
    )
    return deterministic, [exposure], "deterministic incident draft (no verified AI brief available)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--languages", default="hi-IN,mr-IN,ta-IN,te-IN,bn-IN",
        help="Comma-separated Sarvam language codes.",
    )
    args = parser.parse_args()
    targets = [code.strip() for code in args.languages.split(",") if code.strip()]

    text, expected_values, provenance = source_brief()

    if not config.HAS_SARVAM_CREDS:
        OUTPUT.write_text(json.dumps({
            "status": "NOT_RUN",
            "reason": "SARVAM_API_KEY is not set. No translation was produced.",
            "boundary": (
                "VIGIL emits no placeholder or pre-written regional text. Absence of a key means "
                "absence of a translation."
            ),
            "source_brief": text,
            "source_brief_provenance": provenance,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        print("SARVAM_API_KEY is not set; wrote a NOT_RUN localisation record (no fake text).")
        return 1

    results: dict[str, Any] = {}
    for code in targets:
        try:
            translation = translate(text, code)
        except SarvamUnavailable as error:
            results[code] = {"language": LANGUAGES.get(code, code), "status": "FAILED", "error": str(error)[:300]}
            print(f"  {code:6s} FAILED  {error}")
            continue
        check = check_magnitude_survived(translation["translated_text"], expected_values)
        safe = check["status"] == "MAGNITUDE_PRESERVED"
        results[code] = {
            "language": LANGUAGES.get(code, code),
            "status": "TRANSLATED" if safe else "QUARANTINED",
            "translated_text": translation["translated_text"],
            "sarvam_request_ids": translation["request_ids"],
            "magnitude_check": check,
        }
        print(f"  {code:6s} {check['status']}")

    all_safe = len(results) == len(targets) and all(
        item.get("status") == "TRANSLATED" for item in results.values()
    )
    payload = {
        "status": "CAPTURED" if all_safe else "CAPTURED_WITH_FINDINGS",
        "provider": "Sarvam AI",
        "api": f"{config.SARVAM_BASE_URL}/translate",
        "source_language": "en-IN",
        "source_brief": text,
        "source_brief_provenance": provenance,
        "expected_magnitudes_inr": expected_values,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "boundary": (
            "Regional briefs are an internal readability aid for branch and regional staff. "
            "The English draft remains the authoritative record, and nothing here is filed with a regulator."
        ),
        "translations": results,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Safe translations: {sum(1 for r in results.values() if r['status'] == 'TRANSLATED')}/{len(targets)}.")
    print(f"written: {OUTPUT.relative_to(ROOT)}")
    return 0 if all_safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
