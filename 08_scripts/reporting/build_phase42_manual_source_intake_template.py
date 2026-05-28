#!/usr/bin/env python3
"""Build Phase 42 manual source intake template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_manual_source_intake import build_manual_source_intake_template

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str, evidence_type: str) -> dict:
    return build_manual_source_intake_template(ticker, evidence_type)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 manual source intake template")
    parser.add_argument("--ticker", default="300308.SZ")
    parser.add_argument("--evidence-type", default="official_consensus")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.ticker, args.evidence_type)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
