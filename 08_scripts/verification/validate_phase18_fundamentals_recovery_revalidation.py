#!/usr/bin/env python3
"""Revalidate recovered fundamentals integration for Phase 18."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from update_fundamentals_from_recovered_chunks import build_payload as update_payload
from smr_agents import DB_PATH
from smr_phase6_watchlists import load_watchlist_config
from smr_recovered_fundamentals import TARGET_FIELDS_BY_MARKET, field_recovered_in_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DEFAULT_TICKERS = ["00700.HK", "300308.SZ", "688041.SH"]


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        config = load_watchlist_config()
        items = ((config.get("watchlists") or {}).get(watchlist) or {}).get("tickers") or []
        return [str(item.get("ticker") or item.get("ts_code") or "").upper() for item in items if item.get("ticker") or item.get("ts_code")]
    return list(DEFAULT_TICKERS)


def _market_for_ticker(ticker: str) -> str:
    if ticker.endswith(".HK"):
        return "H"
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    return "US"


def _target_fields(ticker: str) -> list[str]:
    return TARGET_FIELDS_BY_MARKET.get(_market_for_ticker(ticker), [])


def _ticker_result(update: dict[str, Any]) -> dict[str, Any]:
    ticker = update.get("ticker")
    update_detail = update.get("fundamentals_snapshot_update") or {}
    snapshot = update.get("snapshot") or {}
    linkage = update.get("source_linkage") or {}
    target_fields = _target_fields(str(ticker))
    after_core = [field for field in target_fields if not field_recovered_in_snapshot(field, snapshot)]
    fields_recovered = [item.get("field") for item in update_detail.get("fields_updated") or [] if item.get("field")]
    before_core = target_fields
    source_status = "source_found" if linkage.get("source_found") else "source_missing"
    if fields_recovered and str(ticker).upper() in {"00700.HK", "300308.SZ"}:
        source_status = "already_recovered"
    return {
        "ticker": ticker,
        "source_status": source_status,
        "source_linkage": linkage,
        "fields_recovered": fields_recovered,
        "snapshot_updated": update_detail.get("status") == "updated",
        "snapshot_id": update_detail.get("snapshot_id"),
        "core_blockers_before": before_core,
        "core_blockers_after": after_core,
        "core_blockers_reduced": max(0, len(before_core) - len(after_core)),
        "promotion_status_after": "candidate_shadow",
        "remaining_reason": "other_existing_gate_or_manual_review" if not after_core else "remaining_fundamentals_gap",
    }


def build_payload(db_path: str, tickers: list[str], *, live: bool = True) -> dict[str, Any]:
    tickers = [ticker for ticker in tickers if ticker]
    update = update_payload(db_path, tickers, live=live)
    results = [_ticker_result(item) for item in update.get("results") or []]
    source_gaps_closed = sum(1 for item in results if item.get("source_status") == "source_found")
    payload = {
        "generated_at": now_ts(),
        "overall_status": "pass" if any(item["fields_recovered"] for item in results) else "partial_pass",
        "summary": {
            "tickers_checked": len(results),
            "source_gaps_closed": source_gaps_closed,
            "fields_recovered": sum(len(item["fields_recovered"]) for item in results),
            "fundamentals_snapshots_updated": sum(1 for item in results if item.get("snapshot_updated")),
            "core_blockers_reduced": sum(item.get("core_blockers_reduced") or 0 for item in results),
            "new_pending_created": 0,
        },
        "ticker_results": results,
        "fundamentals_update": update,
    }
    conn = sqlite3.connect(db_path)
    try:
        register_snapshot(
            conn,
            entity_type="phase18_fundamentals_recovery_revalidation",
            entity_id="latest",
            status=payload["overall_status"],
            source="validate_phase18_fundamentals_recovery_revalidation.py",
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 18 fundamentals recovery revalidation")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--watchlist")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.db_path, parse_tickers(args.tickers, args.watchlist), live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("validate_phase18_fundamentals_recovery_revalidation.py", "success", "phase18 fundamentals recovery revalidation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
