#!/usr/bin/env python3
"""Resolve CNINFO identity and source discovery status for a ticker."""

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
from smr_cninfo_source_identity import resolve_cninfo_source_identity
from smr_financial_statement_source_discovery import discover_financial_statement_sources
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(db_path: str, ticker: str, *, live: bool = True) -> dict:
    ticker = ticker.upper()
    identity = resolve_cninfo_source_identity(ticker)
    conn = sqlite3.connect(db_path)
    try:
        discovery = discover_financial_statement_sources(conn, ticker, live=live)
        source_status = "found" if discovery.get("best_source") else "missing"
        payload = {
            "generated_at": now_ts(),
            "ticker": ticker,
            "market": "CN" if ticker.endswith((".SZ", ".SH", ".BJ")) else "US",
            "source_identity": identity,
            "source_discovery": {
                "status": source_status,
                "sources_found": discovery.get("sources_found") or [],
                "best_source": discovery.get("best_source"),
                "missing_reason": None if source_status == "found" else discovery.get("missing_reason"),
                "suggested_fix": None if source_status == "found" else discovery.get("suggested_fix"),
            },
        }
        register_snapshot(
            conn,
            entity_type="phase18_cninfo_source_identity",
            entity_id=ticker,
            status=identity.get("status") or "unknown",
            source="resolve_cninfo_source_identity.py",
            payload=payload,
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve CNINFO source identity")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.db_path, args.ticker, live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("resolve_cninfo_source_identity.py", "success", "CNINFO source identity resolved", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
