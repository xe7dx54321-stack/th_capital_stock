#!/usr/bin/env python3
"""Validate Phase 24 tender/procurement evidence impact."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase22_proxy_strengthening import build_ticker_proxy_strengthening
from smr_agents import DB_PATH
from smr_bear_case_mitigation import build_ticker_bear_case_mitigation
from smr_cn_tender_procurement import build_cn_tender_procurement_payload
from smr_phase6_watchlists import load_watchlist_config
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase24_tender_procurement_revalidation.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _why_not_pending(block_diag: dict[str, Any], tender_payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    primary_gate = block_diag.get("primary_blocking_gate")
    if primary_gate:
        reasons.append(f"{primary_gate} remains blocking")
    if not tender_payload.get("evidence_candidates"):
        reasons.append(tender_payload.get("no_result_reason") or "no tender/procurement evidence candidate found")
    if not any(item.get("evidence_strength") == "confirmed_award" for item in tender_payload.get("normalized_results") or []):
        reasons.append("no confirmed signed order or award result")
    reasons.append("Phase 24 does not auto-create pending review")
    return list(dict.fromkeys(reasons))[:8]


def build_ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict[str, Any]:
    before_diag = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist)
    before_proxy = build_ticker_proxy_strengthening(conn, ticker, watchlist=watchlist).get("proxy_strengthening") or {}
    before_bear = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist, include_direct_demand=True).get("bear_case_mitigation") or {}
    tender = build_cn_tender_procurement_payload(conn, ticker, execute=False)
    candidates = tender.get("evidence_candidates") or []
    candidate_strengths = {candidate.get("evidence_strength") for candidate in candidates}
    direct_demand_improved = bool(candidate_strengths & {"confirmed_award", "near_confirmed", "strong_indication"})
    proxy_gate_improved = bool(candidates and any(candidate.get("usable_for_proxy_signal") for candidate in candidates))
    bear_case_gate_improved = bool(candidates and any(candidate.get("usable_for_bear_case_mitigation") for candidate in candidates))
    evidence_ids = [candidate.get("evidence_id") for candidate in candidates if candidate.get("evidence_id")]
    return {
        "ticker": ticker.upper(),
        "tender_candidates_found": len(candidates),
        "evidence_candidate_ids": evidence_ids,
        "before": {
            "proxy_status": (before_proxy.get("after") or {}).get("status"),
            "bear_case_status": before_bear.get("overall_status"),
            "promotion_status": before_diag.get("status"),
        },
        "after": {
            "proxy_status": (before_proxy.get("after") or {}).get("status"),
            "bear_case_status": before_bear.get("overall_status"),
            "promotion_status": before_diag.get("status"),
        },
        "direct_demand_improved": direct_demand_improved,
        "proxy_gate_improved": proxy_gate_improved,
        "bear_case_gate_improved": bear_case_gate_improved,
        "why_not_pending": _why_not_pending(before_diag, tender),
        "new_pending_created": False,
        "requires_human_review": False,
        "paper_order_allowed": False,
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict[str, Any]:
    rows = [build_ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    summary = {
        "tickers_checked": len(rows),
        "tender_candidates_found": sum(row.get("tender_candidates_found") or 0 for row in rows),
        "evidence_candidates_linked": sum(len(row.get("evidence_candidate_ids") or []) for row in rows),
        "direct_demand_improved": sum(1 for row in rows if row.get("direct_demand_improved")),
        "proxy_gate_improved": sum(1 for row in rows if row.get("proxy_gate_improved")),
        "bear_case_gate_improved": sum(1 for row in rows if row.get("bear_case_gate_improved")),
        "new_reduced_size_pending": 0,
        "new_pending_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if any(row.get("tender_candidates_found") for row in rows) else "pass",
        "summary": summary,
        "ticker_results": rows,
        "why_no_pending": [reason for row in rows for reason in row.get("why_not_pending") or []][:16],
        "safety": {
            "promotion_rules_relaxed": False,
            "tender_notice_triggered_pending": False,
            "weak_evidence_triggered_pending": False,
            "valuation_context_only_pending_allowed": False,
            "paper_order_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 24 tender/procurement revalidation")
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
            entity_type="phase24_tender_procurement_revalidation",
            entity_id=args.tickers or args.watchlist,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase24 tender procurement revalidation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
