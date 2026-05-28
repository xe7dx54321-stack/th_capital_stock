#!/usr/bin/env python3
"""Build Phase 48 event thesis strength update."""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path: sys.path.insert(0, str(LIB_DIR))

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_thesis_strength_score_update import build_thesis_strength_update

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(ticker=TARGET_REVIEW_TICKER):
    return build_thesis_strength_update(ticker, thesis_delta="unchanged_or_modestly_strengthened")

def render_markdown(payload):
    u = payload.get("thesis_strength_update") or {}
    lines = [f"# Phase 48 Event Thesis Strength Update: {payload.get('ticker')}", "",
             f"- previous_score: {u.get('previous_score')}",
             f"- current_score: {u.get('current_score')}",
             f"- score_delta: {u.get('score_delta')}",
             f"- thesis_delta: {u.get('thesis_delta')}",
             f"- allowed_interpretation: {u.get('allowed_interpretation')}"]
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event thesis strength update")
    p.add_argument("--db-path", default=""); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    payload = build_payload(args.ticker)
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
