#!/usr/bin/env python3
"""Build Phase 46 tracking variables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_paper_watchlist_tracking_variables import build_tracking_variables
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_tracking_variables(ticker)


def render_markdown(payload: dict) -> str:
    lines = [f"# Phase 46 Tracking Variables: {payload.get('ticker')}", "", "## Variables"]
    for row in payload.get("tracking_variables") or []:
        lines.append(f"- {row.get('variable')}: {row.get('current_status')} / {row.get('allowed_usage')}")
        lines.append(f"  Strengthening: {row.get('strengthening_signal')}")
        lines.append(f"  Weakening: {row.get('weakening_signal')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 tracking variables")
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
