#!/usr/bin/env python3
"""Validate Phase 21 demand evidence impact on bear-case mitigation."""

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
from smr_bear_case_mitigation import bear_case_mitigation_improved, build_ticker_bear_case_mitigation
from smr_direct_demand_evidence import extract_direct_demand_evidence, summarize_demand_evidence
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase21_bear_case_demand_mitigation.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> dict:
    before = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist, include_direct_demand=False)
    demand_items = extract_direct_demand_evidence(conn, ticker, limit=24, persist=True)
    after = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist, include_direct_demand=True)
    before_gate = before.get("bear_case_mitigation") or {}
    after_gate = after.get("bear_case_mitigation") or {}
    demand_summary = summarize_demand_evidence(ticker, demand_items)
    remaining = []
    for response in after_gate.get("responses") or []:
        remaining.extend(response.get("missing_evidence") or [])
    return {
        "ticker": ticker,
        "before": {
            "bear_case_status": before_gate.get("overall_status"),
            "residual_risk_level": before_gate.get("overall_residual_risk_level"),
            "blocks_pending": before_gate.get("blocks_pending"),
        },
        "demand_evidence": {
            "evidence_count": demand_summary.get("evidence_count"),
            "independent_source_count": demand_summary.get("independent_source_count"),
            "dominant_direction": demand_summary.get("dominant_direction"),
            "evidence_ids": demand_summary.get("evidence_ids"),
        },
        "after": {
            "bear_case_status": after_gate.get("overall_status"),
            "residual_risk_level": after_gate.get("overall_residual_risk_level"),
            "blocks_pending": after_gate.get("blocks_pending"),
            "allows_reduced_size_pending": after_gate.get("allows_reduced_size_pending"),
        },
        "improved": bear_case_mitigation_improved(after) and before_gate != after_gate,
        "remaining_risks": list(dict.fromkeys(remaining))[:8],
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict:
    rows = [ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    high_before = sum(1 for row in rows if (row.get("before") or {}).get("residual_risk_level") in {"high", "critical"})
    high_after = sum(1 for row in rows if (row.get("after") or {}).get("residual_risk_level") in {"high", "critical"})
    summary = {
        "tickers_checked": len(rows),
        "bear_case_improved": sum(1 for row in rows if row.get("improved")),
        "high_unresolved_before": high_before,
        "high_unresolved_after": high_after,
        "reduced_size_allowed_after": sum(1 for row in rows if (row.get("after") or {}).get("allows_reduced_size_pending")),
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if summary["bear_case_improved"] or high_after <= high_before else "pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "paper_order_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 21 demand mitigation for bear cases")
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
            entity_type="phase21_bear_case_demand_mitigation",
            entity_id=args.tickers or args.watchlist,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase21 bear-case demand mitigation validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
