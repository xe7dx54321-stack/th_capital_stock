#!/usr/bin/env python3
"""Validate Phase 19 recovered-fundamentals promotion impact."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
for path in (LIB_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import (
    build_ticker_block_diagnostics,
    latest_phase18_validation,
    row_for_ticker,
)
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase19_recovered_fundamentals_promotion_impact.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return ["00700.HK", "300308.SZ", "688041.SH"]


def ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> dict:
    diag = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    phase18 = latest_phase18_validation(conn)
    p18_row = row_for_ticker(phase18, ticker)
    return {
        "ticker": ticker,
        "recovered_fields": diag.get("recovered_fields") or p18_row.get("fields_recovered") or [],
        "core_blockers_before": p18_row.get("core_blockers_before") or [],
        "core_blockers_after": diag.get("core_blockers") or p18_row.get("core_blockers_after") or [],
        "promotion_before": p18_row.get("promotion_status_before") or "candidate_shadow",
        "promotion_after": diag.get("status"),
        "why_not_pending": diag.get("why_not_pending"),
        "primary_blocking_gate": diag.get("primary_blocking_gate"),
        "secondary_blocking_gates": diag.get("secondary_blocking_gates") or [],
        "next_fix": diag.get("next_fix") or [],
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict:
    rows = [ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    gates = sorted(set(row.get("primary_blocking_gate") for row in rows if row.get("primary_blocking_gate")))
    summary = {
        "tickers_checked": len(rows),
        "core_blockers_before": sum(len(row.get("core_blockers_before") or []) for row in rows),
        "core_blockers_after": sum(len(row.get("core_blockers_after") or []) for row in rows),
        "new_pending_created": 0,
        "primary_remaining_gates": gates,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if summary["core_blockers_after"] == 0 else "partial_pass",
        "summary": summary,
        "ticker_results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 19 recovered fundamentals promotion impact")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, parse_tickers(args.tickers, args.watchlist if not args.tickers else None), watchlist=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase19_recovered_fundamentals_promotion_impact",
            entity_id=args.watchlist if not args.tickers else args.tickers,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 recovered fundamentals promotion impact validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
