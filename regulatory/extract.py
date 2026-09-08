#!/usr/bin/env python3
"""Turn the fetched regulatory sources into citable, paragraph-level units.

Citation is the whole point. VIGIL must be able to say "this obligation comes from
paragraph 182 of this document, retrieved at this time, with this hash" - so the
unit of the corpus is the numbered paragraph the regulator itself uses, not an
arbitrary fixed-size window.

Standard library only. PDF text is recovered by inflating the content streams and
reading the text-showing operators; that is enough for these born-digital
documents and avoids adding a dependency for six files.
"""
from __future__ import annotations

import html as html_mod
import json
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "regulatory" / "SOURCES.json"
OUT = ROOT / "artifacts" / "regulatory-corpus.ndjson"

# A numbered clause: "182. The bank shall ..." Regulators number their obligations,
# and that number is the citation an auditor will ask for.
PARA_RE = re.compile(r"(?m)(?:(?<=\s)|(?<=^))(\d{1,3})\.\s+(?=[A-Z(“\"])")
MIN_CHARS = 60


def html_to_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return html_mod.unescape(text)


def _looks_like_prose(text: str) -> bool:
    """Reject embedded font programs and image data misread as text.

    A PDF's font files inflate happily and can contain the same byte sequences as
    a content stream, so "it decompressed" is not evidence that it is text. Real
    prose is overwhelmingly printable; glyph tables are not.
    """
    if len(text) < 40:
        return False
    printable = sum(1 for ch in text if ch.isalnum() or ch in " .,;:()-/'\"\n\u2018\u2019\u201c\u201d")
    if printable / len(text) < 0.85:
        return False
    letters = sum(1 for ch in text if ch.isalpha())
    return letters / len(text) >= 0.5


def pdf_to_text(raw: bytes) -> str:
    """Recover text from a born-digital PDF using only zlib and the text operators."""
    out: list[str] = []
    for stream in re.findall(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            data = zlib.decompress(stream.strip(b"\r\n"))
        except zlib.error:
            continue
        # A real content stream sets a font and shows text.
        if b"BT" not in data or b"Tf" not in data or (b"Tj" not in data and b"TJ" not in data):
            continue
        # Judge prose at stream level, not per BT block: a dropped capital or a
        # bullet glyph is often its own tiny block and would fail a prose test on
        # its own, which silently ate the first letter of every bullet.
        parts: list[str] = []
        for chunk in re.findall(rb"BT(.*?)ET", data, re.S):
            for token in re.finditer(rb"\((?:[^()\\]|\\.)*\)|(T\*|Td|TD|TJ|Tj)", chunk):
                literal = token.group(0)
                if literal.startswith(b"("):
                    body = literal[1:-1]
                    body = re.sub(rb"\\([()\\])", rb"\1", body)
                    parts.append(body.decode("latin-1"))
                elif literal in (b"T*", b"Td", b"TD"):
                    parts.append("\n")
        candidate = "".join(parts)
        if _looks_like_prose(candidate):
            out.append(candidate)
    return "\n".join(out)


def normalise(text: str) -> str:
    text = text.replace("­", "").replace("﻿", "")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def split_paragraphs(text: str) -> list[tuple[str | None, str]]:
    """Split on regulator numbering where present, else on blank lines."""
    marks = list(PARA_RE.finditer(text))
    if len(marks) < 5:  # not a numbered instrument; fall back to line blocks
        return [(None, block.strip()) for block in text.split("\n") if len(block.strip()) >= MIN_CHARS]

    units: list[tuple[str | None, str]] = []
    preamble = text[: marks[0].start()].strip()
    if len(preamble) >= MIN_CHARS:
        units.append((None, preamble))
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[mark.end(): end].strip()
        if len(body) >= MIN_CHARS:
            units.append((mark.group(1), body))
    return units


def main() -> int:
    if not MANIFEST.is_file():
        print("Run regulatory/fetch_sources.py first.", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with OUT.open("w", encoding="utf-8") as handle:
        for source in manifest["sources"]:
            if not source.get("ok"):
                continue
            raw = (ROOT / source["cached_as"]).read_bytes()
            text = normalise(html_to_text(raw) if source["kind"] == "html" else pdf_to_text(raw))
            units = split_paragraphs(text)
            numbered = sum(1 for n, _ in units if n)
            print(f"{source['slug']:38} {len(text):>8,} chars  {len(units):>4} units  "
                  f"({numbered} numbered)")

            for index, (number, body) in enumerate(units):
                handle.write(json.dumps({
                    "chunk_id": f"{source['slug']}#{number or f'b{index}'}",
                    "source_slug": source["slug"],
                    "source_url": source["url"],
                    "publisher": source["publisher"],
                    "retrieved_at_utc": source["fetched_at_utc"],
                    "source_sha256": source["sha256"],
                    "paragraph_number": number,
                    "text": body,
                    "synthetic": False,
                    "boundary": "Verbatim public regulatory text, quoted for citation. "
                                "Not legal advice and not a statement that VIGIL files anything.",
                }, ensure_ascii=False) + "\n")
                written += 1

    print(f"\nwrote {written:,} citable units -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
