#!/usr/bin/env python3
"""Build Phase 22 confirmed-demand evidence escalation summary."""

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
from smr_direct_demand_evidence import (
    STRENGTH_RANK,
    escalation_category_for_item,
    extract_direct_demand_evidence,
    normalize_ticker,
    summarize_demand_evidence,
)
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase22_confirmed_demand_evidence.py"

NEAR_CONFIRMED_CATEGORIES = {"signed_contract", "tender_award", "procurement_award"}
FRAMEWORK_CATEGORIES = {"framework_agreement"}
CUSTOMER_CAPEX_CATEGORIES = {"customer_capex"}


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _best_strength(items: list[dict[str, Any]]) -> str:
    return max((str(item.get("demand_strength") or "blocked") for item in items), key=lambda value: STRENGTH_RANK.get(value, 0), default="missing")


def build_ticker_confirmed_demand(conn: sqlite3.Connection, ticker: str, *, limit: int = 40) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    items = extract_direct_demand_evidence(conn, ticker, limit=limit, persist=True)
    summary = summarize_demand_evidence(ticker, items)
    independent_sources = {
        item.get("independent_source_key")
        for item in items
        if item.get("independent_source_key")
        and item.get("independent_source_key") != "watchlist_metadata_patch"
        and item.get("demand_strength") in {"confirmed_order", "strong_indication", "medium_indication"}
    }
    escalation_categories = [escalation_category_for_item(item) for item in items]
    tender_or_procurement_count = sum(1 for category in escalation_categories if category in NEAR_CONFIRMED_CATEGORIES)
    framework_count = sum(1 for category in escalation_categories if category in FRAMEWORK_CATEGORIES)
    customer_capex_count = sum(1 for category in escalation_categories if category in CUSTOMER_CAPEX_CATEGORIES)
    best_strength = _best_strength(items)
    no_confirmed_reason = None
    if summary.get("confirmed_order_count") == 0:
        if tender_or_procurement_count:
            no_confirmed_reason = "tender/procurement evidence found but not enough to treat as signed customer order"
        elif customer_capex_count:
            no_confirmed_reason = "customer/downstream capex found, but no company-specific signed order"
        else:
            no_confirmed_reason = "no signed contract, tender/procurement award, or confirmed customer order found"
    compact_items = [
        {
            "evidence_id": item.get("evidence_id"),
            "category": escalation_category_for_item(item),
            "source_category": item.get("evidence_category"),
            "strength": item.get("demand_strength"),
            "source_quality": item.get("source_quality"),
            "independent_source_key": item.get("independent_source_key"),
            "limitations": item.get("limitations") or [],
        }
        for item in sorted(
            items,
            key=lambda value: (STRENGTH_RANK.get(str(value.get("demand_strength")), 0), str(value.get("source_quality") or "")),
            reverse=True,
        )[:20]
    ]
    return {
        "ticker": ticker,
        "confirmed_demand_evidence": {
            "confirmed_order_count": summary.get("confirmed_order_count") or 0,
            "tender_or_procurement_count": tender_or_procurement_count,
            "framework_agreement_count": framework_count,
            "customer_capex_count": customer_capex_count,
            "management_guidance_count": sum(1 for item in items if item.get("evidence_category") == "management_guidance"),
            "strong_or_medium_indication_count": (summary.get("strong_indication_count") or 0) + (summary.get("medium_indication_count") or 0),
            "independent_source_count": len(independent_sources),
            "best_evidence_strength": best_strength,
            "no_confirmed_order_reason": no_confirmed_reason,
        },
        "items": compact_items,
        "safety": {
            "indication_treated_as_confirmed_order": False,
            "management_commentary_treated_as_order": False,
            "raw_files_persisted": False,
        },
    }


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    rows = [build_ticker_confirmed_demand(conn, ticker) for ticker in parse_tickers(tickers, watchlist)]
    if len(rows) == 1 and tickers:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "confirmed_order_count": sum((row.get("confirmed_demand_evidence") or {}).get("confirmed_order_count") or 0 for row in rows),
            "tender_or_procurement_count": sum((row.get("confirmed_demand_evidence") or {}).get("tender_or_procurement_count") or 0 for row in rows),
            "framework_agreement_count": sum((row.get("confirmed_demand_evidence") or {}).get("framework_agreement_count") or 0 for row in rows),
            "customer_capex_count": sum((row.get("confirmed_demand_evidence") or {}).get("customer_capex_count") or 0 for row in rows),
            "strong_or_medium_indication_count": sum((row.get("confirmed_demand_evidence") or {}).get("strong_or_medium_indication_count") or 0 for row in rows),
        },
        "ticker_results": rows,
        "safety": {
            "indication_treated_as_confirmed_order": False,
            "promotion_rules_relaxed": False,
            "raw_files_persisted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 22 confirmed demand evidence summary")
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
            entity_type="phase22_confirmed_demand_evidence",
            entity_id=args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 confirmed demand evidence built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
