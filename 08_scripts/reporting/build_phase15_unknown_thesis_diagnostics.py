#!/usr/bin/env python3
"""Explain unknown thesis classifications and suggested metadata patches."""

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
from smr_phase6_watchlists import watchlist_map
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts
from build_phase14_thesis_aware_daily_summary import latest_phase14_validation


SCRIPT_NAME = "build_phase15_unknown_thesis_diagnostics.py"


def _watchlist_lookup(watchlist_id: str) -> dict[str, dict[str, Any]]:
    return watchlist_map(watchlist_id)


def _row_for_ticker(validation: dict[str, Any], ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    for row in validation.get("tickers") or []:
        if str(row.get("ticker") or "").upper() == ticker:
            return row
    return {}


def unknown_reasons(row: dict[str, Any], watchlist_item: dict[str, Any]) -> list[str]:
    inference = row.get("thesis_inference") or {}
    reasons = []
    if float(inference.get("confidence") or row.get("thesis_inference_confidence") or 0.0) < 0.5:
        reasons.append("low_thesis_inference_confidence")
    if not inference.get("inferred_thesis_types"):
        reasons.append("insufficient_claim_graph")
    if not watchlist_item.get("theme") or str(watchlist_item.get("theme")).lower() in {"unknown", "ai_application"}:
        reasons.append("weak_watchlist_metadata")
    if not inference.get("signals_used") or inference.get("signals_used") == ["valuation_related_text"]:
        reasons.append("no_dominant_proxy_signal")
    if row.get("data_quality_gate") == "blocked":
        reasons.append("field_dependency_requires_manual_review")
    return list(dict.fromkeys(reasons or ["manual_thesis_review_required"]))


def suggested_patch(ticker: str, watchlist_item: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    theme = str(watchlist_item.get("theme") or "").lower()
    if ticker.endswith((".SZ", ".SH")) and ("ai" in theme or "application" in theme):
        return {
            "theme": "ai_infrastructure",
            "candidate_thesis_types": ["ai_infrastructure_demand", "revenue_growth"],
            "primary_business_driver": "AI infrastructure or application revenue driver needs explicit confirmation",
        }
    scorecard = (row.get("thesis_inference") or {}).get("scorecard") or {}
    candidates = [name for name, _score in sorted(scorecard.items(), key=lambda item: -float(item[1]))[:2]]
    return {
        "theme": watchlist_item.get("theme") or "needs_manual_theme_tag",
        "candidate_thesis_types": candidates or ["revenue_growth"],
        "primary_business_driver": "add claim keywords or watchlist thesis metadata",
    }


def build_ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist_id: str = "ai_core") -> dict[str, Any]:
    ticker = ticker.upper()
    validation = latest_phase14_validation(conn, watchlist_id)
    lookup = _watchlist_lookup(watchlist_id)
    row = _row_for_ticker(validation, ticker)
    watchlist_item = lookup.get(ticker) or {}
    inference = row.get("thesis_inference") or {}
    confidence = inference.get("confidence") if inference.get("confidence") is not None else row.get("thesis_inference_confidence")
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "current_thesis_type": row.get("primary_thesis_type") or "unknown",
        "inference_confidence": confidence,
        "unknown_reasons": unknown_reasons(row, watchlist_item),
        "missing_inputs": [
            item
            for item in ["theme_tag", "primary_business_driver", "claim_keywords"]
            if item == "claim_keywords" or not watchlist_item.get("theme")
        ],
        "signals_used": inference.get("signals_used") or [],
        "scorecard": inference.get("scorecard") or {},
        "suggested_metadata_patch": suggested_patch(ticker, watchlist_item, row),
        "allow_pending": False,
    }


def build_watchlist_payload(conn: sqlite3.Connection, watchlist_id: str) -> dict[str, Any]:
    validation = latest_phase14_validation(conn, watchlist_id)
    rows = validation.get("tickers") or []
    unknown = [row for row in rows if row.get("primary_thesis_type") == "unknown"]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist_id,
        "unknown_thesis_count": len(unknown),
        "items": [build_ticker_payload(conn, str(row.get("ticker")), watchlist_id=watchlist_id) for row in unknown],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 15 unknown thesis diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_ticker_payload(conn, args.ticker, watchlist_id=args.watchlist) if args.ticker else build_watchlist_payload(conn, args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase15_unknown_thesis_diagnostics",
            entity_id=(args.ticker or args.watchlist).upper() if args.ticker else args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase15 unknown thesis diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
