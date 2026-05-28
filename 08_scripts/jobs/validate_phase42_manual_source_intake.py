#!/usr/bin/env python3
"""Validate Phase 42 manual source intake sample payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_manual_source_intake_validator import sample_intake, validate_manual_source_intake

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(sample: str) -> dict:
    intake = sample_intake(sample)
    result = validate_manual_source_intake(intake)
    return {"sample": sample, "intake": intake, **result}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 42 manual source intake")
    parser.add_argument("--sample", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.sample)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
