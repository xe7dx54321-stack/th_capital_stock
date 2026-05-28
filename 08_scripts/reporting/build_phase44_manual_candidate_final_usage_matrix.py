#!/usr/bin/env python3
"""Build Phase 44 final usage matrix for reviewed manual candidates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_manual_candidate_review_lifecycle import (
    FINAL_LIMITATIONS_BY_CANDIDATE_TYPE,
    list_lifecycles,
)
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ORDER = {"official_consensus": 0, "supplier_share": 1, "customer_allocation": 2}


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    lifecycles = sorted(list_lifecycles(conn, ticker=ticker), key=lambda row: ORDER.get(str(row.get("candidate_type")), 99))
    rows = []
    for item in lifecycles:
        candidate_type = item.get("candidate_type")
        limitations = list(dict.fromkeys((item.get("limitations") or []) + FINAL_LIMITATIONS_BY_CANDIDATE_TYPE.get(candidate_type, [])))
        rows.append(
            {
                "candidate_type": candidate_type,
                "candidate_id": item.get("candidate_id"),
                "review_status": item.get("status"),
                "confirmation_status": item.get("confirmation_status"),
                "final_allowed_usage": item.get("allowed_usage"),
                "final_limitations": limitations,
                "usable_for_promotion": False,
                "pending_allowed": False,
                "paper_order_allowed": False,
            }
        )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_candidate_final_usage_matrix": {
            "candidate_count": len(rows),
            "confirmed_variables_added": 0,
            "usable_for_promotion_true": 0,
            "pending_created": 0,
            "paper_order_created": 0,
            "rows": rows,
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
    body = payload.get("manual_candidate_final_usage_matrix") or {}
    lines = [f"# Phase 44 Manual Candidate Final Usage Matrix: {payload.get('ticker')}", "", "## Summary"]
    for key in ("candidate_count", "confirmed_variables_added", "usable_for_promotion_true", "pending_created", "paper_order_created"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Rows"])
    for row in body.get("rows") or []:
        lines.append(f"- {row.get('candidate_type')}: {row.get('review_status')} / {row.get('final_allowed_usage')}")
        lines.append(f"  Limitations: {', '.join(row.get('final_limitations') or [])}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 44 final usage matrix")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
