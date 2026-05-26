#!/usr/bin/env python3
"""Build Phase 21 direct demand evidence summary."""

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
from smr_direct_demand_evidence import build_direct_demand_evidence_payload
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase21_direct_demand_evidence_summary.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    rows = [build_direct_demand_evidence_payload(conn, ticker, limit=30, persist=True) for ticker in parse_tickers(tickers, watchlist)]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "direct_demand_evidence_count": sum((row.get("demand_evidence_summary") or {}).get("evidence_count") or 0 for row in rows),
            "confirmed_order_count": sum((row.get("demand_evidence_summary") or {}).get("confirmed_order_count") or 0 for row in rows),
            "strong_indication_count": sum((row.get("demand_evidence_summary") or {}).get("strong_indication_count") or 0 for row in rows),
            "medium_indication_count": sum((row.get("demand_evidence_summary") or {}).get("medium_indication_count") or 0 for row in rows),
            "usable_for_proxy_signal": sum(1 for row in rows if (row.get("demand_evidence_summary") or {}).get("usable_for_proxy_signal")),
            "usable_for_bear_case_mitigation": sum(
                1 for row in rows if (row.get("demand_evidence_summary") or {}).get("usable_for_bear_case_mitigation")
            ),
        },
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "direct_demand_auto_pending": False,
            "raw_files_persisted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 21 direct demand evidence summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase21_direct_demand_evidence_summary",
            entity_id=args.tickers or args.watchlist,
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase21 direct demand evidence summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
