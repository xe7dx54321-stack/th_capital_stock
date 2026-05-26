#!/usr/bin/env python3
"""Build Phase 26 consensus / expectation proxy packs."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_supply_chain_variable_evidence import build_consensus_expectation_proxy_pack
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase26_consensus_expectation_proxy.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(ticker or tickers)
    rows = [{"ticker": item, "consensus_expectation_proxy": build_consensus_expectation_proxy_pack(conn, item)} for item in resolved]
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "official_consensus_available": sum(1 for row in rows if row["consensus_expectation_proxy"].get("official_consensus_available")),
            "internal_proxy_available": sum(1 for row in rows if row["consensus_expectation_proxy"].get("internal_proxy_available")),
            "official_consensus_fabricated": 0,
        },
        "rows": rows,
    }
    if len(rows) == 1 and ticker and not tickers:
        return {**rows[0], "generated_at": payload["generated_at"]}
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 26 consensus / expectation proxy")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
        register_snapshot(conn, "phase26_consensus_expectation_proxy", args.ticker or args.tickers or "supply_chain_pilot", "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase26 consensus expectation proxy built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
