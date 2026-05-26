#!/usr/bin/env python3
"""Extract Phase 21 direct demand evidence from existing local evidence."""

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
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_direct_demand_evidence.py"


def parse_tickers(raw: str | None, ticker: str | None = None) -> list[str]:
    if ticker:
        return [ticker.strip().upper()]
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    return []


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, limit: int = 40) -> dict:
    rows = [build_direct_demand_evidence_payload(conn, ticker, limit=limit, persist=True) for ticker in tickers]
    if len(rows) == 1:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "direct_demand_evidence_count": sum((row.get("demand_evidence_summary") or {}).get("evidence_count") or 0 for row in rows),
            "confirmed_order_count": sum((row.get("demand_evidence_summary") or {}).get("confirmed_order_count") or 0 for row in rows),
            "strong_or_medium_indication_count": sum(
                ((row.get("demand_evidence_summary") or {}).get("strong_indication_count") or 0)
                + ((row.get("demand_evidence_summary") or {}).get("medium_indication_count") or 0)
                for row in rows
            ),
            "tickers_with_usable_bear_case_evidence": sum(
                1 for row in rows if (row.get("demand_evidence_summary") or {}).get("usable_for_bear_case_mitigation")
            ),
            "tickers_with_usable_proxy_evidence": sum(
                1 for row in rows if (row.get("demand_evidence_summary") or {}).get("usable_for_proxy_signal")
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
    parser = argparse.ArgumentParser(description="Build Phase 21 direct demand evidence")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    tickers = parse_tickers(args.tickers, args.ticker)
    if not tickers:
        raise SystemExit("--ticker or --tickers is required")
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers, limit=args.limit)
        register_snapshot(
            conn,
            entity_type="phase21_direct_demand_evidence",
            entity_id=args.ticker or args.tickers,
            status="extracted",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase21 direct demand evidence extracted", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
