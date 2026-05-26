#!/usr/bin/env python3
"""Build Phase 21 demand/proxy gate summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_registry import register_snapshot
from smr_runlog import log_run
from validate_phase21_promotion_revalidation import build_payload as build_revalidation
from validate_phase21_promotion_revalidation import parse_tickers

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase21_demand_proxy_gate_summary.py"


def _primary_gate(row: dict) -> str:
    if row.get("bear_case_status_after") in {"requires_more_evidence", "unresolved_core"}:
        return "BEAR_CASE_GATE"
    if row.get("valuation_status_after") in {"blocked", "insufficient", "context_only"}:
        return "VALUATION_GATE"
    if row.get("proxy_status_after") in {"weak", "missing", "invalid", "conflicted"}:
        return "PROXY_SIGNAL_GATE"
    if row.get("after_status") == "pending_human_review":
        return "REVIEW_STATE_GATE"
    return row.get("primary_gate_before") or "UNKNOWN_GATE"


def compact_payload(revalidation: dict, watchlist: str) -> dict:
    distribution: dict[str, list[str]] = defaultdict(list)
    rows = []
    missing_rows = []
    for item in revalidation.get("ticker_results") or []:
        gate = _primary_gate(item)
        distribution[gate].append(item.get("ticker"))
        next_fix = (item.get("why_no_pending") or ["inspect remaining demand/proxy gate"])[0]
        rows.append(
            {
                "ticker": item.get("ticker"),
                "direct_demand_evidence": item.get("direct_demand_best_strength") or "missing",
                "independent_source_count": item.get("proxy_sources_after") or 0,
                "proxy_status": item.get("proxy_status_after"),
                "bear_case_status": item.get("bear_case_status_after"),
                "valuation_status": item.get("valuation_status_after"),
                "promotion_status": item.get("after_status"),
                "primary_gate": gate,
                "next_fix": next_fix,
            }
        )
        for warning in item.get("remaining_warnings") or []:
            missing_rows.append(
                {
                    "ticker": item.get("ticker"),
                    "missing_evidence": warning,
                    "suggested_source": "annual report / latest news / procurement or customer evidence",
                }
            )
    summary = revalidation.get("summary") or {}
    return {
        "generated_at": revalidation.get("generated_at"),
        "summary": {
            "watchlist_id": watchlist,
            "tickers": len(rows),
            "direct_demand_evidence_count": summary.get("direct_demand_evidence_added") or 0,
            "proxy_sources_expanded": summary.get("proxy_sources_expanded") or 0,
            "bear_case_improved": summary.get("bear_case_gate_improved") or 0,
            "new_reduced_size_pending": summary.get("new_reduced_size_pending") or 0,
            "primary_remaining_gates": {gate: len(tickers) for gate, tickers in distribution.items()},
        },
        "rows": rows,
        "remaining_missing_evidence": missing_rows[:40],
        "gate_distribution": {gate: tickers for gate, tickers in distribution.items()},
        "safety": revalidation.get("safety") or {},
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 21 Demand / Proxy Gate Summary",
        "",
        "## Overall",
        f"- Direct demand evidence found: {summary.get('direct_demand_evidence_count')}",
        f"- Proxy sources expanded: {summary.get('proxy_sources_expanded')}",
        f"- Bear cases improved: {summary.get('bear_case_improved')}",
        f"- New reduced-size pending: {summary.get('new_reduced_size_pending')}",
        "",
        "## By Ticker",
        "| Ticker | Demand Evidence | Proxy | Bear Case | Promotion | Next Fix |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('direct_demand_evidence')} | "
            f"{row.get('proxy_status')} ({row.get('independent_source_count')} sources) | "
            f"{row.get('bear_case_status')} | {row.get('promotion_status')} | {row.get('next_fix')} |"
        )
    lines.extend(["", "## Remaining Missing Evidence", "| Ticker | Missing Evidence | Suggested Source |", "|---|---|---|"])
    for row in payload.get("remaining_missing_evidence") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('missing_evidence')} | {row.get('suggested_source')} |")
    return "\n".join(lines).rstrip() + "\n"


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    return compact_payload(build_revalidation(conn, parse_tickers(tickers, watchlist), watchlist=watchlist), watchlist)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 21 demand/proxy gate summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase21_demand_proxy_gate_summary",
            entity_id=args.watchlist,
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase21 demand/proxy gate summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
