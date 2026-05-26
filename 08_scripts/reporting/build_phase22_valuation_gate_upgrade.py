#!/usr/bin/env python3
"""Build Phase 22 valuation gate v2 diagnostics."""

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
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation_gate_v2 import diagnose_valuation_gate_v2, valuation_gate_v2_improved
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase22_valuation_gate_upgrade.py"


def parse_tickers(raw: str | None, ticker: str | None = None, watchlist: str | None = None) -> list[str]:
    if ticker:
        return [ticker.strip().upper()]
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(
    conn: sqlite3.Connection,
    *,
    watchlist: str = "ai_core",
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict:
    rows = [diagnose_valuation_gate_v2(conn, item, watchlist_id=watchlist) for item in parse_tickers(tickers, ticker, watchlist if not ticker and not tickers else None)]
    if len(rows) == 1 and ticker:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "valuation_gate_improved": sum(1 for row in rows if valuation_gate_v2_improved(row)),
            "promotion_supporting": sum(1 for row in rows if (row.get("valuation_gate_v2") or {}).get("after_status") == "promotion_supporting"),
            "reduced_size_supporting": sum(1 for row in rows if (row.get("valuation_gate_v2") or {}).get("after_status") == "reduced_size_supporting"),
            "supporting_evidence": sum(1 for row in rows if (row.get("valuation_gate_v2") or {}).get("after_status") == "supporting_evidence"),
            "context_or_blocked": sum(1 for row in rows if (row.get("valuation_gate_v2") or {}).get("after_status") in {"context_only", "insufficient", "blocked"}),
        },
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "proxy_eps_official_consensus": False,
            "valuation_context_only_pending_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 22 valuation gate upgrade diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, ticker=args.ticker, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase22_valuation_gate_upgrade",
            entity_id=args.ticker or args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 valuation gate upgrade built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
