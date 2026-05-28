#!/usr/bin/env python3
"""Build Phase 46 paper watchlist audit report."""

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
from smr_paper_watchlist_audit import list_paper_watchlist_audits
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    records = list_paper_watchlist_audits(conn, ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "watchlist_audit_report": {
            "audit_records": len(records),
            "pending_created": sum(1 for row in records if row.get("pending_created")),
            "paper_order_created": sum(1 for row in records if row.get("paper_order_created")),
            "real_trade_created": sum(1 for row in records if row.get("real_trade_created")),
            "records": records,
        },
        "safety": {
            "audit_connects_to_promotion_gate": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("watchlist_audit_report") or {}
    lines = [f"# Phase 46 Watchlist Audit Report: {payload.get('ticker')}", "", "## Summary"]
    for key in ("audit_records", "pending_created", "paper_order_created", "real_trade_created"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Records"])
    for row in body.get("records") or []:
        lines.append(f"- {row.get('action')}: {row.get('before_status')} -> {row.get('after_status')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 watchlist audit report")
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
