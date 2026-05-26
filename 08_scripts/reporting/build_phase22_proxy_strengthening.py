#!/usr/bin/env python3
"""Build Phase 22 proxy source strengthening diagnostics."""

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

from build_phase21_proxy_source_expansion import build_ticker_proxy_source_expansion, parse_tickers
from smr_agents import DB_PATH
from smr_direct_demand_evidence import extract_direct_demand_evidence
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase22_proxy_strengthening.py"


def _phase22_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _source_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        if not item.get("usable_for_proxy_signal") or not item.get("evidence_id"):
            continue
        rows.append(
            {
                "evidence_id": item.get("evidence_id"),
                "source_key": item.get("independent_source_key"),
                "quality": item.get("source_quality"),
                "thesis_alignment": "strong" if item.get("claim_relevance") == "core" else "partial",
                "demand_strength": item.get("demand_strength"),
                "internal_proxy": True,
            }
        )
    return rows[:10]


def build_ticker_proxy_strengthening(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict[str, Any]:
    base = build_ticker_proxy_source_expansion(conn, ticker, watchlist=watchlist)
    demand_items = extract_direct_demand_evidence(conn, ticker, limit=30, persist=True)
    after = base.get("after") or {}
    remaining = list(after.get("remaining_requirements") or [])
    if after.get("proxy_status") != "strong" and "stronger direct demand evidence" not in remaining:
        remaining.append("stronger direct demand evidence")
    if after.get("proxy_status") in {"weak", "missing", "invalid", "conflicted"} and "weak proxy cannot support pending" not in remaining:
        remaining.append("weak proxy cannot support pending")
    return {
        "ticker": ticker.upper(),
        "proxy_strengthening": {
            "before": {
                "status": (base.get("before") or {}).get("proxy_status"),
                "independent_source_count": (base.get("before") or {}).get("independent_source_count"),
                "proxy_strength_score": (base.get("before") or {}).get("proxy_strength_score"),
            },
            "after": {
                "status": after.get("proxy_status"),
                "independent_source_count": after.get("independent_source_count"),
                "proxy_strength_score": after.get("proxy_strength_score"),
                "usable_for_reduced_size_pending": after.get("usable_for_reduced_size_pending"),
                "is_official_consensus": False,
            },
            "sources_added": _source_rows(demand_items),
            "remaining_requirements": list(dict.fromkeys(remaining)),
            "safety": {
                "internal_proxy_only": True,
                "official_consensus_active": False,
                "weak_proxy_pending_allowed": False,
                "promotion_rules_relaxed": False,
            },
        },
    }


def proxy_strengthened(row: dict[str, Any]) -> bool:
    gate = row.get("proxy_strengthening") or {}
    before = gate.get("before") or {}
    after = gate.get("after") or {}
    status_rank = {"missing": 0, "invalid": 0, "conflicted": 0, "weak": 1, "medium": 2, "strong": 3}
    return (
        status_rank.get(str(after.get("status") or "missing"), 0) > status_rank.get(str(before.get("status") or "missing"), 0)
        or int(after.get("independent_source_count") or 0) > int(before.get("independent_source_count") or 0)
    )


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict[str, Any]:
    rows = [build_ticker_proxy_strengthening(conn, ticker, watchlist=watchlist) for ticker in _phase22_tickers(tickers, watchlist)]
    if len(rows) == 1 and tickers:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "proxy_strengthened": sum(1 for row in rows if proxy_strengthened(row)),
            "strong": sum(1 for row in rows if ((row.get("proxy_strengthening") or {}).get("after") or {}).get("status") == "strong"),
            "medium": sum(1 for row in rows if ((row.get("proxy_strengthening") or {}).get("after") or {}).get("status") == "medium"),
            "weak_or_missing": sum(
                1
                for row in rows
                if ((row.get("proxy_strengthening") or {}).get("after") or {}).get("status") in {"weak", "missing", "invalid", "conflicted"}
            ),
        },
        "ticker_results": rows,
        "safety": {
            "internal_proxy_only": True,
            "promotion_rules_relaxed": False,
            "weak_proxy_pending_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 22 proxy strengthening diagnostics")
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
            entity_type="phase22_proxy_strengthening",
            entity_id=args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 proxy strengthening built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
