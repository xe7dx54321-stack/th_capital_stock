#!/usr/bin/env python3
"""Build Phase 46 thesis strength tracking score."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_thesis_strength_tracking import build_thesis_strength_tracking

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_thesis_strength_tracking(ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("thesis_strength_tracking") or {}
    lines = [
        f"# Phase 46 Thesis Strength Score: {payload.get('ticker')}",
        "",
        f"- thesis_strength_score: {body.get('thesis_strength_score')}",
        f"- thesis_strength_bucket: {body.get('thesis_strength_bucket')}",
        f"- allowed_interpretation: {body.get('allowed_interpretation')}",
        "",
        "## Positive Contributors",
    ]
    lines.extend(f"- {item}" for item in body.get("positive_contributors") or [])
    lines.extend(["", "## Negative Or Unconfirmed Contributors"])
    lines.extend(f"- {item}" for item in body.get("negative_or_unconfirmed_contributors") or [])
    lines.extend(["", "## Forbidden Interpretation"])
    lines.extend(f"- {item}" for item in body.get("forbidden_interpretation") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 thesis strength score")
    parser.add_argument("--db-path", default=str(DB_PATH), help="Accepted for CLI consistency; not read by this report")
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
