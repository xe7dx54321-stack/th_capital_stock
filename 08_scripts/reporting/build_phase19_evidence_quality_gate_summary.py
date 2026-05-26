#!/usr/bin/env python3
"""Build Phase 19 evidence quality gate summary."""

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
from smr_evidence_quality import build_evidence_quality_gate
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase19_evidence_quality_gate_summary.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", ticker: str | None = None, tickers: str | None = None) -> dict:
    if ticker:
        return build_evidence_quality_gate(conn, ticker)
    full_rows = [build_evidence_quality_gate(conn, item) for item in parse_tickers(tickers, watchlist)]
    rows = [
        {
            "ticker": row.get("ticker"),
            "evidence_quality_gate": row.get("evidence_quality_gate") or {},
            "evidence_sample": (row.get("evidence") or [])[:5],
        }
        for row in full_rows
    ]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "pass": sum(1 for row in rows if (row.get("evidence_quality_gate") or {}).get("status") == "pass"),
            "pass_with_warnings": sum(1 for row in rows if (row.get("evidence_quality_gate") or {}).get("status") == "pass_with_warnings"),
            "blocked": sum(1 for row in rows if (row.get("evidence_quality_gate") or {}).get("status") == "blocked"),
            "high_quality_evidence_count": sum((row.get("evidence_quality_gate") or {}).get("high_quality_evidence_count") or 0 for row in rows),
        },
        "ticker_results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 19 evidence quality gate summary")
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
            entity_type="phase19_evidence_quality_gate_summary",
            entity_id=(args.ticker or args.tickers or args.watchlist),
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 evidence quality gate summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
