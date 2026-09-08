#!/usr/bin/env python3
"""Dependency-free Amazon Bedrock client for the VIGIL rehearsal.

Design notes that matter for the judge Q&A:

* **No model is assumed.** ``BEDROCK_MODEL_ID`` may be pinned, but by default the
  client lists the account's cross-region inference profiles and on-demand text
  models, then *tries to invoke* them in preference order. Listing a model does not
  prove access is granted, so only a successful invocation is recorded.
* **Amazon Nova only by default.** The hackathon deployment deliberately avoids an
  Anthropic dependency. In Mumbai, Bedrock can expose Nova through an ``apac.``
  cross-region inference profile, so those profile IDs are preferred over direct
  foundation-model IDs.
* **Output is capped.** ``maxTokens`` defaults to 600 and temperature to 0, so a
  rehearsal run costs a fraction of a rupee and is reproducible.
* **The Converse API is used for Nova.** Models that reject a separate system
  prompt or a zero temperature are retried with a reduced request rather than
  silently skipped.
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from llm.sigv4 import canonical_path, encode_path_segment, sign_request

# Cheapest-capable first. Cross-region profile IDs are tried before direct model
# IDs because ap-south-1 commonly exposes Nova through APAC inference profiles.
PREFERRED_MODELS: tuple[str, ...] = (
    "apac.amazon.nova-micro-v1:0",
    "apac.amazon.nova-lite-v1:0",
    "apac.amazon.nova-2-lite-v1:0",
    "global.amazon.nova-2-lite-v1:0",
    "amazon.nova-micro-v1:0",
    "amazon.nova-lite-v1:0",
    "amazon.nova-2-lite-v1:0",
)

# Published on-demand USD per million tokens, used only to print a cost estimate so a
# free-tier run is provably negligible. Unknown models report "unpriced", never zero.
PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "amazon.nova-micro-v1:0": (0.035, 0.14),
    "amazon.nova-lite-v1:0": (0.06, 0.24),
}


class BedrockUnavailable(RuntimeError):
    """Raised when no candidate model could actually be invoked."""


class BedrockError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        safe_body = _safe_error(body)
        super().__init__(f"HTTP {status}: {safe_body[:400]}")
        self.status = status
        self.body = safe_body


def _safe_error(value: str) -> str:
    """Keep useful AWS diagnostics without printing account or credential identifiers."""
    value = re.sub(r"(?<!\d)\d{12}(?!\d)", "<aws-account-id>", value)
    return re.sub(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "<aws-access-key-id>", value)


def _tls_context() -> ssl.SSLContext:
    # python.org macOS installers can have no populated OpenSSL cert directory even
    # though macOS maintains a system PEM bundle. Prefer Python's configured trust
    # store, then use that system bundle; verification is never disabled.
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile or defaults.capath:
        return ssl.create_default_context()
    system_bundle = Path("/etc/ssl/cert.pem")
    return ssl.create_default_context(cafile=str(system_bundle) if system_bundle.exists() else None)


def _request(
    *,
    method: str,
    host: str,
    wire_path: str,
    query_string: str = "",
    body: bytes = b"",
    service: str = "bedrock",
    double_encode: bool,
) -> tuple[int, str]:
    if not config.HAS_AWS_CREDS:
        raise BedrockUnavailable(
            "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are not set; see .env.example."
        )
    extra = {"content-type": "application/json"} if body else {}
    headers = sign_request(
        method=method,
        host=host,
        request_path=wire_path,
        canonical_uri=canonical_path(wire_path, double_encode=double_encode),
        query_string=query_string,
        body=body,
        region=config.AWS_REGION,
        service=service,
        access_key=config.AWS_ACCESS_KEY_ID,
        secret_key=config.AWS_SECRET_ACCESS_KEY,
        session_token=config.AWS_SESSION_TOKEN,
        extra_headers=extra,
    )
    url = f"https://{host}{wire_path}"
    if query_string:
        url = f"{url}?{query_string}"
    request = urllib.request.Request(url, data=body or None, method=method.upper())
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=60, context=_tls_context()) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:  # surfaced, never swallowed
        return error.code, error.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise BedrockUnavailable(f"Bedrock unreachable: {error.reason}") from None


def list_on_demand_text_models() -> list[str]:
    """Return model ids this region offers on demand for text output.

    Availability is not the same as access. The returned list is a candidate set.
    """
    status, body = _request(
        method="GET",
        host=f"bedrock.{config.AWS_REGION}.amazonaws.com",
        wire_path="/foundation-models",
        query_string="byInferenceType=ON_DEMAND&byOutputModality=TEXT",
        double_encode=True,
    )
    if status != 200:
        raise BedrockError(status, body)
    payload = json.loads(body)
    return [
        entry["modelId"]
        for entry in payload.get("modelSummaries", [])
        if entry.get("modelLifecycle", {}).get("status") == "ACTIVE"
    ]


def list_system_inference_profiles() -> list[str]:
    """Return cross-region inference profile IDs visible to this AWS identity."""
    status, body = _request(
        method="GET",
        host=f"bedrock.{config.AWS_REGION}.amazonaws.com",
        wire_path="/inference-profiles",
        query_string="maxResults=1000&type=SYSTEM_DEFINED",
        double_encode=True,
    )
    if status != 200:
        raise BedrockError(status, body)
    payload = json.loads(body)
    return [
        entry["inferenceProfileId"]
        for entry in payload.get("inferenceProfileSummaries", [])
        if entry.get("status") == "ACTIVE" and entry.get("inferenceProfileId")
    ]


def _converse_body(prompt: str, system: str | None, max_tokens: int, temperature: float | None) -> bytes:
    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    if temperature is not None:
        payload["inferenceConfig"]["temperature"] = temperature
    if system:
        payload["system"] = [{"text": system}]
    return json.dumps(payload).encode("utf-8")


def _converse_once(model_id: str, body: bytes) -> tuple[int, str]:
    wire_path = f"/model/{encode_path_segment(model_id)}/converse"
    host = f"bedrock-runtime.{config.AWS_REGION}.amazonaws.com"
    status, response = _request(
        method="POST", host=host, wire_path=wire_path, body=body,
        service="bedrock", double_encode=True,
    )
    # Canonical-path encoding depth is the one part of SigV4 that varies by endpoint.
    # Rather than assume, fall back to the single-encoded form on a signature failure.
    if status == 403 and "SignatureDoesNotMatch" in response:
        status, response = _request(
            method="POST", host=host, wire_path=wire_path, body=body,
            service="bedrock", double_encode=False,
        )
    return status, response


def converse(
    prompt: str,
    *,
    system: str | None = None,
    model_id: str | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Invoke the first candidate model this account can actually call.

    Returns the text plus a provenance block recording the real model id, region,
    token usage, measured latency and every candidate that refused the call.
    """
    max_tokens = max_tokens or config.BEDROCK_MAX_OUTPUT_TOKENS
    pinned = model_id or config.BEDROCK_MODEL_ID
    if pinned:
        candidates = [pinned]
    else:
        offered: set[str] = set()
        try:
            offered.update(list_system_inference_profiles())
        except (BedrockError, BedrockUnavailable) as error:
            print(f"note: inference-profile discovery unavailable ({error}).")
        try:
            offered.update(list_on_demand_text_models())
        except (BedrockError, BedrockUnavailable) as error:
            print(f"note: foundation-model discovery unavailable ({error}).")
        # Discovery can be denied while invocation is allowed, so try the known
        # preference order blind only when neither control-plane call succeeded.
        candidates = [m for m in PREFERRED_MODELS if not offered or m in offered]

    if not candidates:
        raise BedrockUnavailable(
            f"No preferred on-demand text model is offered in {config.AWS_REGION}. "
            "Set BEDROCK_MODEL_ID explicitly."
        )

    refusals: list[dict[str, str]] = []
    for candidate in candidates:
        for attempt_system, attempt_temperature in (
            (system, 0.0),          # normal path
            (system, None),         # model rejects temperature 0
            (None, 0.0),            # model rejects a separate system prompt
        ):
            merged_prompt = prompt if attempt_system or not system else f"{system}\n\n{prompt}"
            body = _converse_body(merged_prompt, attempt_system, max_tokens, attempt_temperature)
            started = time.perf_counter()
            status, response = _converse_once(candidate, body)
            elapsed_ms = int((time.perf_counter() - started) * 1000)

            if status == 200:
                parsed = json.loads(response)
                text = "".join(
                    part.get("text", "")
                    for part in parsed.get("output", {}).get("message", {}).get("content", [])
                )
                usage = parsed.get("usage", {})
                price_in, price_out = PRICING_USD_PER_MTOK.get(candidate, (None, None))
                cost_usd = None
                if price_in is not None:
                    cost_usd = round(
                        usage.get("inputTokens", 0) / 1_000_000 * price_in
                        + usage.get("outputTokens", 0) / 1_000_000 * price_out,
                        8,
                    )
                return {
                    "text": text.strip(),
                    "provenance": {
                        "provider": "AWS Bedrock",
                        "api": "Converse",
                        "model_id": candidate,
                        "region": config.AWS_REGION,
                        "system_prompt_supported": attempt_system is not None,
                        "temperature": attempt_temperature,
                        "max_output_tokens": max_tokens,
                        "input_tokens": usage.get("inputTokens"),
                        "output_tokens": usage.get("outputTokens"),
                        "total_tokens": usage.get("totalTokens"),
                        "stop_reason": parsed.get("stopReason"),
                        "measured_latency_ms": elapsed_ms,
                        "reported_latency_ms": parsed.get("metrics", {}).get("latencyMs"),
                        "estimated_cost_usd": cost_usd if cost_usd is not None else "unpriced",
                        "candidates_refused": refusals,
                    },
                }

            note = {
                "model_id": candidate,
                "status": str(status),
                "error": _safe_error(response[:200]),
            }
            if status == 400 and "ValidationException" in response:
                continue  # try a reduced request shape against the same model
            refusals.append(note)
            break  # access/throttle problem: move to the next model

        else:
            refusals.append({"model_id": candidate, "status": "400", "error": "all request shapes rejected"})

    raise BedrockUnavailable(
        "No candidate Bedrock model accepted the request. Refusals: "
        + json.dumps(refusals, indent=2)
    )


def main() -> int:
    """`python3 llm/bedrock.py` — prove connectivity and print what this account can call."""
    print(f"region              : {config.AWS_REGION}")
    print(f"credentials         : {'configured' if config.HAS_AWS_CREDS else 'not configured'}")
    print(f"pinned model        : {config.BEDROCK_MODEL_ID or '<none: auto-discover>'}")
    if not config.HAS_AWS_CREDS:
        print("\nAWS credentials are not set. Add them to .env (see .env.example).")
        return 1
    try:
        profiles = list_system_inference_profiles()
        nova_profiles = [profile for profile in profiles if ".amazon.nova" in profile]
        print(f"\nactive Nova inference profiles: {len(nova_profiles)}")
        for profile in nova_profiles:
            print(f"  {profile}")
    except (BedrockError, BedrockUnavailable) as error:
        print(f"\ninference-profile discovery failed: {error}")
    try:
        available = list_on_demand_text_models()
        print(f"\non-demand text models offered in region: {len(available)}")
        for model in PREFERRED_MODELS:
            print(f"  {'offered ' if model in available else 'absent  '} {model}")
    except (BedrockError, BedrockUnavailable) as error:
        print(f"\ndiscovery failed: {error}")
    try:
        result = converse(
            "Reply with exactly: VIGIL Bedrock connectivity confirmed.",
            system="You are a terse connectivity probe.",
            max_tokens=32,
        )
    except BedrockUnavailable as error:
        print(f"\nINVOCATION FAILED\n{error}")
        return 1
    print(f"\nmodel invoked       : {result['provenance']['model_id']}")
    print(f"response            : {result['text']}")
    print(f"tokens in/out       : {result['provenance']['input_tokens']}/{result['provenance']['output_tokens']}")
    print(f"latency             : {result['provenance']['measured_latency_ms']} ms")
    print(f"estimated cost      : USD {result['provenance']['estimated_cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
