#!/usr/bin/env python3
"""Build Phase 45 final review dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase45_final_research_conclusion import build_payload as build_conclusion
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    ticker = "300308.SZ"
    conclusion = build_conclusion(conn, ticker).get("final_research_conclusion") or {}
    return {
        "generated_at": now_ts(),
        "summary": {
            "ticker": ticker,
            "conclusion_status": conclusion.get("conclusion_status"),
            "paper_watchlist_readiness": conclusion.get("paper_watchlist_readiness"),
            "conclusion_confidence": conclusion.get("conclusion_confidence"),
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_allowed_true": 0,
            "next_phase": "phase46_paper_watchlist_tracking",
        },
        "safety": {
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    lines = ["# Phase 45 Final Review Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final review dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
