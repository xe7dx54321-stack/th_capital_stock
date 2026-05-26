#!/usr/bin/env python3
"""Build Phase 21 independent proxy source expansion diagnostics."""

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
from smr_direct_demand_evidence import extract_direct_demand_evidence, summarize_demand_evidence
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_proxy_signal_gate import build_proxy_signal_gate, evaluate_proxy_signal_gate, latest_proxy_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase21_proxy_source_expansion.py"


def parse_tickers(raw: str | None, ticker: str | None = None, watchlist: str | None = None) -> list[str]:
    if ticker:
        return [ticker.strip().upper()]
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _source_keys_for_evidence(conn: sqlite3.Connection, evidence_ids: list[str]) -> set[str]:
    if not evidence_ids:
        return set()
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name='evidence_items'").fetchone():
        return set()
    placeholders = ",".join("?" for _ in evidence_ids)
    return {
        str(row[0])
        for row in conn.execute(f"SELECT DISTINCT source_key FROM evidence_items WHERE evidence_id IN ({placeholders})", tuple(evidence_ids)).fetchall()
        if row[0]
    }


def _quality_from_demand(items: list[dict[str, Any]], fallback: str = "blocked") -> str:
    ranks = {"blocked": 0, "low": 1, "medium": 2, "high": 3}
    best = ranks.get(str(fallback or "blocked"), 0)
    for item in items:
        if item.get("usable_for_proxy_signal"):
            best = max(best, ranks.get(str(item.get("source_quality") or "blocked"), 0))
    for value, rank in ranks.items():
        if rank == best:
            return value
    return "blocked"


def _direction_from_summary(summary: dict[str, Any], base_direction: str | None) -> str:
    if summary.get("dominant_direction") == "positive":
        return "up"
    if summary.get("dominant_direction") == "negative":
        return "down"
    return str(base_direction or "unknown")


def expand_proxy_snapshot_with_demand(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    base_snapshot: dict[str, Any],
    demand_items: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    usable = [item for item in demand_items if item.get("usable_for_proxy_signal") and item.get("evidence_id")]
    summary = summarize_demand_evidence(ticker, demand_items)
    base_evidence_ids = list(dict.fromkeys(base_snapshot.get("evidence_ids") or []))
    demand_evidence_ids = list(dict.fromkeys(str(item.get("evidence_id")) for item in usable if item.get("evidence_id")))
    combined_evidence_ids = list(dict.fromkeys(base_evidence_ids + demand_evidence_ids))
    base_source_keys = _source_keys_for_evidence(conn, base_evidence_ids)
    demand_source_keys = {
        str(item.get("independent_source_key"))
        for item in usable
        if item.get("independent_source_key") and item.get("independent_source_key") != "watchlist_metadata_patch"
    }
    base_independent_count = int(base_snapshot.get("independent_source_count") or 0)
    if base_source_keys:
        independent_count = max(len(base_source_keys | demand_source_keys), base_independent_count)
    else:
        independent_count = base_independent_count + len(demand_source_keys)
    independent_count = max(independent_count, len(demand_source_keys))
    demand_confidence = 0.0
    if summary.get("best_demand_strength") == "confirmed_order":
        demand_confidence = 0.82
    elif summary.get("best_demand_strength") == "strong_indication":
        demand_confidence = 0.74
    elif summary.get("best_demand_strength") == "medium_indication":
        demand_confidence = 0.64
    elif summary.get("best_demand_strength") == "weak_indication":
        demand_confidence = 0.48
    synthetic_signals = [
        {
            "signal_id": f"demand_proxy_{item.get('demand_evidence_id')}",
            "direction": "up" if item.get("demand_direction") == "positive" else "down" if item.get("demand_direction") == "negative" else "unknown",
            "source_evidence_id": item.get("evidence_id"),
            "source_type": item.get("source_type"),
            "confidence": demand_confidence,
            "metadata": {
                "internal_proxy_only": True,
                "demand_strength": item.get("demand_strength"),
                "independent_source_key": item.get("independent_source_key"),
            },
        }
        for item in usable[:8]
    ]
    expanded = {
        **base_snapshot,
        "proxy_direction": _direction_from_summary(summary, base_snapshot.get("proxy_direction")),
        "confidence": max(float(base_snapshot.get("confidence") or 0.0), demand_confidence),
        "evidence_ids": combined_evidence_ids,
        "evidence_count": len(combined_evidence_ids),
        "independent_source_count": independent_count,
        "signals": list(base_snapshot.get("signals") or []) + synthetic_signals,
        "evidence_quality_override": _quality_from_demand(usable),
        "direct_demand_evidence_ids": demand_evidence_ids,
    }
    added = {
        "independent_sources_added": max(0, independent_count - int(base_snapshot.get("independent_source_count") or 0)),
        "evidence_ids": demand_evidence_ids,
        "dominant_direction": summary.get("dominant_direction"),
        "best_demand_strength": summary.get("best_demand_strength"),
        "internal_proxy": True,
    }
    return expanded, added


def build_ticker_proxy_source_expansion(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict[str, Any]:
    ticker = ticker.upper()
    diag = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    before_gate = build_proxy_signal_gate(conn, ticker, watchlist_id=watchlist).get("proxy_signal_gate") or {}
    base_snapshot = latest_proxy_snapshot(conn, ticker)
    demand_items = extract_direct_demand_evidence(
        conn,
        ticker,
        thesis_type=str(diag.get("primary_thesis_type") or "unknown"),
        limit=24,
        persist=True,
    )
    expanded_snapshot, added = expand_proxy_snapshot_with_demand(conn, ticker=ticker, base_snapshot=base_snapshot, demand_items=demand_items)
    after_gate = evaluate_proxy_signal_gate(conn, ticker, thesis_type=diag.get("primary_thesis_type"), snapshot=expanded_snapshot).get("proxy_signal_gate") or {}
    remaining = list(after_gate.get("missing_requirements") or [])
    if after_gate.get("status") != "strong" and "proxy_not_official_consensus" not in remaining:
        remaining.append("proxy_not_official_consensus")
    return {
        "ticker": ticker,
        "before": {
            "proxy_status": before_gate.get("status"),
            "independent_source_count": before_gate.get("independent_source_count"),
            "proxy_strength_score": before_gate.get("proxy_strength_score"),
        },
        "demand_evidence_added": added,
        "after": {
            "proxy_status": after_gate.get("status"),
            "independent_source_count": after_gate.get("independent_source_count"),
            "proxy_strength_score": after_gate.get("proxy_strength_score"),
            "usable_for_promotion": after_gate.get("usable_for_promotion"),
            "usable_for_reduced_size_pending": after_gate.get("usable_for_reduced_size_pending"),
            "remaining_requirements": remaining,
            "is_official_consensus": False,
            "note": "internal_proxy only; not official consensus",
        },
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict[str, Any]:
    rows = [build_ticker_proxy_source_expansion(conn, ticker, watchlist=watchlist) for ticker in tickers]
    if len(rows) == 1:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "proxy_sources_expanded": sum(1 for row in rows if (row.get("demand_evidence_added") or {}).get("independent_sources_added")),
            "strong": sum(1 for row in rows if (row.get("after") or {}).get("proxy_status") == "strong"),
            "medium": sum(1 for row in rows if (row.get("after") or {}).get("proxy_status") == "medium"),
            "weak_or_missing": sum(
                1 for row in rows if (row.get("after") or {}).get("proxy_status") in {"weak", "missing", "invalid", "conflicted"}
            ),
        },
        "ticker_results": rows,
        "safety": {
            "internal_proxy_only": True,
            "official_consensus_active": False,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 21 proxy source expansion diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    tickers = parse_tickers(args.tickers, args.ticker, args.watchlist if not args.ticker and not args.tickers else None)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers, watchlist=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase21_proxy_source_expansion",
            entity_id=args.ticker or args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase21 proxy source expansion built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
