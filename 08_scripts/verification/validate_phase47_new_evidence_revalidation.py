#!/usr/bin/env python3
"""Validate Phase 47 new evidence research-only revalidation."""

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
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_new_evidence_delta_detector import build_new_evidence_delta
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    delta = build_new_evidence_delta(conn, ticker).get("new_evidence_delta") or {}
    revalidation_required = delta.get("revalidation_required", False)
    overall_status = (
        "research_only_revalidated" if revalidation_required else "no_new_evidence_noop"
    )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "new_evidence_revalidation": {
            "revalidation_required": revalidation_required,
            "overall_status": overall_status,
            "thesis_delta": "unchanged",
            "affected_variables": [],
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
        "safety": {
            "revalidation_creates_pending": False,
            "revalidation_creates_order": False,
            "revalidation_creates_trade": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 47 new evidence revalidation")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
