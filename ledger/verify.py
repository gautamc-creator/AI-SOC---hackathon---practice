#!/usr/bin/env python3
"""Standalone VIGIL evidence-ledger verifier; deliberately has no app dependencies."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chain import GENESIS_HASH, validate_block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    blocks = json.loads(args.ledger.read_text(encoding="utf-8"))
    previous = GENESIS_HASH
    for expected_sequence, block in enumerate(blocks):
        issue = validate_block(block, expected_sequence, previous)
        if issue:
            print(f"FAIL: block {expected_sequence}: {issue}")
            return 1
        previous = block["hash"]
    print(f"PASS: {len(blocks)} evidence blocks verified; final hash {previous}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
