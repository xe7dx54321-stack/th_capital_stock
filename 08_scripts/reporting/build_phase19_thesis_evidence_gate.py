#!/usr/bin/env python3
"""Build Phase 19 thesis evidence gate diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase15_unknown_thesis_diagnostics import build_ticker_payload as build_phase15_ticker_payload
from smr_agents import DB_PATH
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase19_thesis_evidence_gate.py"


def required_evidence_for(thesis: str) -> list[str]:
    if thesis == "ai_infrastructure_demand":
        return [
            "revenue_growth_evidence",
            "order_or_demand_evidence",
            "AI infrastructure business driver evidence",
        ]
    if thesis == "valuation_rerating":
        return ["valuation_support", "fresh_price_evidence", "bear_case_response_evidence"]
    return ["claim_graph_support", "filing_or_news_support", "dominant_proxy_signal"]


def build_ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist_id: str = "ai_core") -> dict[str, Any]:
    base = build_phase15_ticker_payload(conn, ticker, watchlist_id=watchlist_id)
    after = base.get("after_patch_simulation") or {}
    candidate = after.get("candidate_thesis_type") or base.get("current_thesis_type") or "unknown"
    confidence = float(after.get("simulated_confidence") or base.get("inference_confidence") or 0.0)
    available = []
    if base.get("suggested_metadata_patch"):
        available.append("watchlist_metadata")
    signals = base.get("signals_used") or after.get("signals_used") or []
    if signals and signals != ["valuation_related_text"]:
        available.append("thesis_inference_signal")
    missing = ["claim_graph_support", "dominant_proxy_signal", "filing_or_news_support"]
    if candidate == "unknown" and confidence < 0.5:
        status = "unknown_thesis"
        next_fix = ["improve watchlist thesis metadata", "add claim graph support"]
    else:
        status = "evidence_insufficient"
        next_fix = ["build claim graph from financial statement / news evidence", "extract proxy signal for AI infrastructure demand"]
    return {
        "ticker": ticker.upper(),
        "before": {
            "primary_thesis_type": base.get("current_thesis_type") or "unknown",
            "confidence": base.get("inference_confidence"),
            "allow_pending": False,
        },
        "after_metadata_simulation": {
            "candidate_thesis_type": candidate,
            "confidence": confidence,
            "allow_pending": False,
        },
        "thesis_evidence_gate": {
            "status": status,
            "required_evidence": required_evidence_for(candidate),
            "available_evidence": available,
            "missing_evidence": missing,
            "next_fix": next_fix,
        },
    }


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", ticker: str | None = None) -> dict[str, Any]:
    if ticker:
        return build_ticker_payload(conn, ticker, watchlist_id=watchlist)
    rows = [build_ticker_payload(conn, item, watchlist_id=watchlist) for item in parse_tickers(None, watchlist)]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "evidence_insufficient": sum(1 for row in rows if (row.get("thesis_evidence_gate") or {}).get("status") == "evidence_insufficient"),
            "unknown_thesis": sum(1 for row in rows if (row.get("thesis_evidence_gate") or {}).get("status") == "unknown_thesis"),
            "new_pending_created": 0,
        },
        "ticker_results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 19 thesis evidence gate diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, ticker=args.ticker)
        register_snapshot(
            conn,
            entity_type="phase19_thesis_evidence_gate",
            entity_id=(args.ticker or args.watchlist),
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 thesis evidence gate diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
