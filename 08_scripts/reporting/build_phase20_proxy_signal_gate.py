#!/usr/bin/env python3
"""Build Phase 20 proxy signal gate diagnostics."""

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
from smr_proxy_signal_gate import build_proxy_signal_gate, proxy_gate_improved
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase20_proxy_signal_gate.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", ticker: str | None = None, tickers: str | None = None) -> dict:
    if ticker:
        return build_proxy_signal_gate(conn, ticker, watchlist_id=watchlist)
    rows = [build_proxy_signal_gate(conn, item, watchlist_id=watchlist) for item in parse_tickers(tickers, watchlist)]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "proxy_gate_improved": sum(1 for row in rows if proxy_gate_improved(row)),
            "strong": sum(1 for row in rows if (row.get("proxy_signal_gate") or {}).get("status") == "strong"),
            "medium": sum(1 for row in rows if (row.get("proxy_signal_gate") or {}).get("status") == "medium"),
            "weak_or_missing": sum(1 for row in rows if (row.get("proxy_signal_gate") or {}).get("status") in {"weak", "missing", "invalid", "conflicted"}),
        },
        "ticker_results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 20 proxy signal gate diagnostics")
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
            entity_type="phase20_proxy_signal_gate",
            entity_id=args.ticker or args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase20 proxy signal gate diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
