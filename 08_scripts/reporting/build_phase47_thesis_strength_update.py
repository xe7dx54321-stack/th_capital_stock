#!/usr/bin/env python3
"""Build Phase 47 thesis strength update."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_thesis_strength_score_update import build_thesis_strength_update

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str = TARGET_REVIEW_TICKER, thesis_delta: str = "unchanged") -> dict:
    return build_thesis_strength_update(ticker, thesis_delta=thesis_delta)


def render_markdown(payload: dict) -> str:
    update = payload.get("thesis_strength_update") or {}
    lines = [
        f"# Phase 47 Thesis Strength Update: {payload.get('ticker')}",
        "",
        f"- previous_score: {update.get('previous_score')}",
        f"- current_score: {update.get('current_score')}",
        f"- score_delta: {update.get('score_delta')}",
        f"- previous_bucket: {update.get('previous_bucket')}",
        f"- current_bucket: {update.get('current_bucket')}",
        f"- thesis_delta: {update.get('thesis_delta')}",
        f"- allowed_interpretation: {update.get('allowed_interpretation')}",
        "",
        "## Forbidden Interpretation",
    ]
    for item in update.get("forbidden_interpretation") or []:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 thesis strength update")
    parser.add_argument("--db-path", default="", help="Accepted for CLI consistency")
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
