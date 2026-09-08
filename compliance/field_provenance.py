#!/usr/bin/env python3
"""Field-by-field provenance inspector for VIGIL's regulatory drafts.

For every field in incident-report-draft.json, cert-in-incident-form-draft.json
and rbi-daksh-information-pack.json, this records: which source produced it,
whether that source is observed telemetry, a deterministic calculation, a
hardcoded constant, an LLM-generated narrative, or an intentionally blank
analyst-required slot — and whether the field must NEVER be populated by an
LLM. This is a manual audit of report/generate.py and compliance/generate.py,
encoded as data, plus a cross-check that the evidence-derived headline exposure
matches the independently recorded observed total. The fixture answer key is an
assertion in report/generate.py, never the displayed value's source.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"

# classification values:
#   observed             -> read directly from a telemetry/event field
#   calculated            -> deterministic code computes it from observed data
#   hardcoded_constant     -> a literal string/number in source, not derived from this run's data
#   analyst_required       -> intentionally blank; only an authorised human may fill it
#   not_observed           -> intentionally explicit "not present in this fixture", not fabricated
#   llm_generated          -> produced by Attack Discovery; unverified until a human reviews it
#   system_generated       -> a process timestamp/id, not a fact about the incident itself
PROVENANCE = [
    {"artifact": "incident-report-draft.json", "field": "classification",
     "classification": "calculated", "confidence": "not_scored", "never_llm_infer": True,
     "source": "workflow/classify.py: deterministic tag-pattern classifier over evidence events.",
     "note": None},
    {"artifact": "incident-report-draft.json", "field": "occurrence_start_timestamp_utc",
     "classification": "observed", "confidence": "high", "never_llm_infer": True,
     "source": "min(event['@timestamp']) over the hero evidence events.", "note": None},
    {"artifact": "incident-report-draft.json", "field": "first_observed_timestamp_utc",
     "classification": "observed", "confidence": "high", "never_llm_infer": True,
     "source": "min(event['event']['created']) over the hero evidence events.", "note": None},
    {"artifact": "incident-report-draft.json", "field": "cert_in_notice_anchor_utc",
     "classification": "system_generated", "confidence": "low", "never_llm_infer": True,
     "source": "report/generate.py: datetime.now() at report-generation time.",
     "note": "This is process/generation time, NOT a verified human 'noticed_at' timestamp. Per "
             "docs/JUDGE-READINESS and the RBI 2026 Directions, the CERT-In clock must start from when a human "
             "actually noticed the incident, which can differ from when this draft happened to be generated. "
             "An analyst must confirm or override this value before it is used as a filing clock anchor."},
    {"artifact": "incident-report-draft.json", "field": "affected_asset",
     "classification": "observed", "confidence": "high", "never_llm_infer": True,
     "source": "ground-truth.json hero.host, itself copied from the generator's HERO_HOST constant.", "note": None},
    {"artifact": "incident-report-draft.json", "field": "affected_service",
     "classification": "calculated", "confidence": "high", "never_llm_infer": True,
     "source": "report/generate.py: exact host.name join against bank-context.ndjson, then vigil.bank.service.",
     "note": "Report generation fails closed unless exactly one context row matches the evidence-derived host."},
    {"artifact": "incident-report-draft.json", "field": "deterministic_exposure_inr",
     "classification": "calculated", "confidence": "high (for this fixture)", "never_llm_infer": True,
     "source": "report/generate.py: sum(event['vigil']['transaction']['amount']) over the sealed hero evidence events.",
     "note": "The generator's expected_exposure_inr is used only as a test oracle. Report generation fails closed "
             "if the evidence-derived value disagrees with that answer key."},
    {"artifact": "incident-report-draft.json", "field": "observed_suspicious_upi_total_inr",
     "classification": "calculated", "confidence": "high", "never_llm_infer": True,
     "source": "report/generate.py: sum(event['vigil']['transaction']['amount']) over hero evidence events.",
     "note": None},
    {"artifact": "incident-report-draft.json", "field": "evidence_event_ids",
     "classification": "observed", "confidence": "high", "never_llm_infer": True,
     "source": "ground-truth.json hero.event_ids, filtered against the actual events.ndjson rows present.", "note": None},
    {"artifact": "incident-report-draft.json", "field": "evidence_envelope.evidence_set_hash",
     "classification": "calculated", "confidence": "high", "never_llm_infer": True,
     "source": "workflow/gather_evidence.py: SHA-256 over the canonical evidence event list.", "note": None},
    {"artifact": "incident-report-draft.json", "field": "attack_discovery.*",
     "classification": "llm_generated", "confidence": "unverified", "never_llm_infer": "n/a — this IS the LLM output",
     "source": "Elastic Security Attack Discovery (Elastic-managed connector; not yet AWS Bedrock).",
     "note": "Human review required before any fact in this block is treated as established. Never copy this text "
             "directly into a filed regulatory report."},
    {"artifact": "incident-report-draft.json", "field": "attack_discovery_claim_review.*",
     "classification": "calculated", "confidence": "phrase-level heuristic, not semantic", "never_llm_infer": True,
     "source": "workflow/review_discovery.py: deterministic regex phrase check over the captured AD text.",
     "note": "This guardrail must itself stay deterministic; if it were ever reimplemented with an LLM it would "
             "lose its value as an independent check on LLM overclaim."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "reporting_party.*",
     "classification": "analyst_required", "confidence": "n/a", "never_llm_infer": True,
     "source": "compliance/generate.py: literal \"REQUIRED BEFORE SUBMISSION\".",
     "note": "Correct design: reporter identity must never be auto-populated or LLM-inferred. Keep this."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "incident_type",
     "classification": "calculated", "confidence": "medium — analyst confirmation required", "never_llm_infer": True,
     "source": "compliance/generate.py: deterministic mapping from vigil.bank.regulated_channel in the joined context row.",
     "note": "The draft records this mapping's provenance and still requires an authorised analyst to confirm applicability."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "mission_critical_system.value",
     "classification": "calculated", "confidence": "high for fixture context", "never_llm_infer": True,
     "source": "compliance/generate.py: vigil.bank.criticality from the exact host bank-context join.",
     "note": "Anything other than mission_critical becomes 'No / requires analyst confirmation'."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "affected_system.ip_address",
     "classification": "not_observed", "confidence": "n/a", "never_llm_infer": True,
     "source": "compliance/generate.py: explicit NOT OBSERVED; the event source IP is not assumed to be the host's own address.",
     "note": "Source and destination IPs remain available separately under technical_information."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "affected_system.{domain_or_url,operating_system,cloud_or_make_model,location,network_or_isp}",
     "classification": "not_observed", "confidence": "n/a", "never_llm_infer": True,
     "source": "compliance/generate.py: literal \"NOT OBSERVED IN FIXTURE\" / \"NOT APPLICABLE — synthetic\".",
     "note": "Correct design: explicit, non-fabricated absence rather than an invented value. Keep this pattern."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "symptoms_observed",
     "classification": "calculated", "confidence": "high", "never_llm_infer": True,
     "source": "compliance/generate.py: counts grouped by structured event.action and event.outcome over sealed evidence ids.",
     "note": "Raw message text is intentionally excluded so prompt-injection content cannot become a report fact."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "technical_information.{source_ips,external_source_ips,destination_ips}",
     "classification": "observed", "confidence": "high", "never_llm_infer": True,
     "source": "compliance/generate.py: unique structured source.ip/destination.ip values over sealed evidence ids.",
     "note": "External source values require vigil.security.source_zone == external; no address is copied from a literal."},
    {"artifact": "cert-in-incident-form-draft.json", "field": "submission_status",
     "classification": "hardcoded_constant", "confidence": "n/a", "never_llm_infer": True,
     "source": "compliance/generate.py: literal \"NOT SUBMITTED\".",
     "note": "Correct and must stay hardcoded in the prototype; never make this dynamic/configurable."},
    {"artifact": "rbi-daksh-information-pack.json", "field": "exposure_inr",
     "classification": "calculated", "confidence": "high (for this fixture)", "never_llm_infer": True,
     "source": "Same evidence-derived provenance as incident-report-draft.json's deterministic_exposure_inr.",
     "note": "See the cross-check above."},
    {"artifact": "rbi-daksh-information-pack.json", "field": "submission_status",
     "classification": "hardcoded_constant", "confidence": "n/a", "never_llm_infer": True,
     "source": "compliance/generate.py: literal \"NOT SUBMITTED\".", "note": "Must stay hardcoded."},
]


def get_path(obj: Any, path: str) -> Any:
    for part in path.split("."):
        if part.endswith("]") and "[" in part:
            continue  # not used; kept simple for the flat fields inspected here
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def main() -> None:
    report_path = ARTIFACTS / "incident-report-draft.json"
    if not report_path.exists():
        print("Run `make demo` first so incident-report-draft.json exists.")
        raise SystemExit(1)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    cross_check = {
        "check": "deterministic_exposure_inr vs observed_suspicious_upi_total_inr",
        "deterministic_exposure_inr": report.get("deterministic_exposure_inr"),
        "observed_suspicious_upi_total_inr": report.get("observed_suspicious_upi_total_inr"),
        "agree": report.get("deterministic_exposure_inr") == report.get("observed_suspicious_upi_total_inr"),
    }

    by_classification: dict[str, int] = {}
    for row in PROVENANCE:
        by_classification[row["classification"]] = by_classification.get(row["classification"], 0) + 1

    result = {
        "status": "FIELD PROVENANCE AUDIT — not a substitute for legal/compliance sign-off",
        "cross_check": cross_check,
        "fields_by_classification": by_classification,
        "hardcoded_will_not_generalize": [row["field"] for row in PROVENANCE if row["classification"] == "hardcoded_constant"],
        "llm_generated_fields": [row["field"] for row in PROVENANCE if row["classification"] == "llm_generated"],
        "fields": PROVENANCE,
    }
    (ARTIFACTS / "field-provenance-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    md = ["# VIGIL field-provenance audit", "",
          f"Cross-check: `deterministic_exposure_inr` ({cross_check['deterministic_exposure_inr']}) vs "
          f"`observed_suspicious_upi_total_inr` ({cross_check['observed_suspicious_upi_total_inr']}) — "
          f"**{'AGREE' if cross_check['agree'] else 'DISAGREE — investigate immediately'}**.", "",
          "| Artifact | Field | Classification | Never LLM-inferred | Note |", "|---|---|---|---|---|"]
    for row in PROVENANCE:
        note = (row["note"] or "").replace("\n", " ")
        md.append(f"| {row['artifact']} | {row['field']} | {row['classification']} | {row['never_llm_infer']} | {note} |")
    md += ["", f"Fields by classification: {json.dumps(by_classification)}", "",
           f"Hardcoded constants that will not generalize past the hero scenario: "
           f"{len(result['hardcoded_will_not_generalize'])} fields."]
    (ARTIFACTS / "FIELD-PROVENANCE-AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Cross-check {'PASSED' if cross_check['agree'] else 'FAILED'}: exposure figures "
          f"{'agree' if cross_check['agree'] else 'DISAGREE'}.")
    print(f"Wrote artifacts/field-provenance-report.json and artifacts/FIELD-PROVENANCE-AUDIT.md "
          f"({len(PROVENANCE)} fields audited, {len(result['hardcoded_will_not_generalize'])} hardcoded).")
    if not cross_check["agree"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
