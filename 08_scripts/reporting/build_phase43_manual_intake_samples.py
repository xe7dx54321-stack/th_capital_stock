#!/usr/bin/env python3
"""Build Phase 43 manual intake sample payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_manual_intake_payload import build_manual_intake_samples_payload
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str) -> dict:
    return build_manual_intake_samples_payload(ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("manual_intake_samples") or {}
    lines = [f"# Phase 43 Manual Intake Samples: {payload.get('ticker')}", "", "## Samples"]
    for row in body.get("samples") or []:
        lines.append(f"- {row.get('intake_id')}: {row.get('evidence_type')} / {row.get('source_type')}")
        lines.append(f"  Permission: {row.get('permission_status')}")
        lines.append(f"  Requested usage: {row.get('requested_allowed_usage')}")
        lines.append(f"  Limitations: {', '.join(row.get('limitations') or [])}")
    lines.extend(
        [
            "",
            "## Safety",
            "- sample payloads are not real data",
            "- raw_file_attached=false",
            "- no evidence, pending review, paper order, or promotion is created",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 manual intake samples")
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.ticker)
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
