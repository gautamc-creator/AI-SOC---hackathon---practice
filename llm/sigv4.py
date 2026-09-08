#!/usr/bin/env python3
"""Minimal AWS Signature Version 4 signer built only on the standard library.

The rest of this repository is dependency-free on purpose, so Bedrock is reached
by signing requests here rather than by installing boto3. This implements the
documented SigV4 flow for a JSON request and nothing else: no retries with
backoff, no credential-provider chain, no service-specific quirks beyond the
canonical-path encoding note below.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
from typing import Mapping
from urllib.parse import quote

ALGORITHM = "AWS4-HMAC-SHA256"


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def encode_path_segment(segment: str) -> str:
    """Percent-encode one path segment for the wire (e.g. a Bedrock model id)."""
    return quote(segment, safe="")


def canonical_path(request_path: str, double_encode: bool) -> str:
    """Return the path as it must appear inside the canonical request.

    AWS documents that every path segment is URI-encoded twice for all services
    except Amazon S3, which is why ``double_encode`` re-encodes the already
    percent-encoded wire path. Signing is sensitive enough that
    :func:`llm.bedrock.invoke` tries the single-encoded form as a fallback rather
    than relying on this being right for every endpoint.
    """
    if not double_encode:
        return request_path
    return quote(request_path, safe="/~")


def signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    key = _hmac(f"AWS4{secret_key}".encode("utf-8"), date_stamp)
    key = _hmac(key, region)
    key = _hmac(key, service)
    return _hmac(key, "aws4_request")


def sign_request(
    *,
    method: str,
    host: str,
    request_path: str,
    canonical_uri: str,
    query_string: str = "",
    body: bytes = b"",
    region: str,
    service: str,
    access_key: str,
    secret_key: str,
    session_token: str = "",
    extra_headers: Mapping[str, str] | None = None,
    now: _dt.datetime | None = None,
) -> dict[str, str]:
    """Return the headers required to authenticate a single request.

    ``request_path`` is what goes on the wire; ``canonical_uri`` is what goes into
    the string to sign. They differ only in percent-encoding depth.
    """
    moment = now or _dt.datetime.now(_dt.timezone.utc)
    amz_date = moment.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = moment.strftime("%Y%m%d")
    payload_hash = _sha256_hex(body)

    headers: dict[str, str] = {
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
    }
    if session_token:
        headers["x-amz-security-token"] = session_token
    for key, value in (extra_headers or {}).items():
        headers[key.lower()] = value

    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{key}:{headers[key].strip()}\n" for key in sorted(headers))
    canonical_request = "\n".join([
        method.upper(),
        canonical_uri,
        query_string,
        canonical_headers,
        signed_headers,
        payload_hash,
    ])

    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join([
        ALGORITHM,
        amz_date,
        scope,
        _sha256_hex(canonical_request.encode("utf-8")),
    ])
    signature = hmac.new(
        signing_key(secret_key, date_stamp, region, service),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    headers["authorization"] = (
        f"{ALGORITHM} Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return headers
