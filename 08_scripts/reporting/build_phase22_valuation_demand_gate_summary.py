#!/usr/bin/env python3
"""Build Phase 22 valuation/demand gate summary."""

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
from validate_phase22_valuation_demand_promotion_revalidation import build_payload as build_revalidation
from validate_phase22_valuation_demand_promotion_revalidation import parse_tickers

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase22_valuation_demand_gate_summary.py"


def _primary_gate(row: dict) -> str:
    if row.get("after_status") == "pending_human_review":
        return "REVIEW_STATE_GATE"
    if row.get("valuation_after") in {"blocked", "insufficient", "context_only"}:
        return "VALUATION_GATE"
    if row.get("proxy_after") in {"weak", "missing", "invalid", "conflicted"}:
        return "PROXY_SIGNAL_GATE"
    if row.get("bear_case_status_after") in {"requires_more_evidence", "unresolved_core"}:
        return "BEAR_CASE_GATE"
    if row.get("valuation_after") == "supporting_evidence":
        return "VALUATION_GATE"
    return row.get("primary_gate_before") or "UNKNOWN_GATE"


def compact_payload(revalidation: dict, watchlist: str) -> dict:
    distribution: dict[str, list[str]] = defaultdict(list)
    rows = []
    blocker_rows = []
    for item in revalidation.get("ticker_results") or []:
        gate = _primary_gate(item)
        distribution[gate].append(item.get("ticker"))
        next_fix = (item.get("why_no_pending") or ["inspect remaining valuation/demand gate"])[0]
        demand_label = item.get("demand_valuation_linkage") or "missing"
        confirmed = bool((item.get("confirmed_order_count") or 0) > 0)
        rows.append(
            {
                "ticker": item.get("ticker"),
                "valuation_status": item.get("valuation_after"),
                "demand_evidence": demand_label,
                "confirmed_order": confirmed,
                "proxy_status": item.get("proxy_after"),
                "promotion_status": item.get("after_status"),
                "primary_gate": gate,
                "next_fix": next_fix,
            }
        )
        for warning in item.get("remaining_warnings") or []:
            if "VALUATION" in str(warning) or "valuation" in str(warning) or "EPS" in str(warning) or "DEMAND" in str(warning):
                blocker_rows.append({"ticker": item.get("ticker"), "blocker": warning, "suggested_fix": next_fix})
    summary = revalidation.get("summary") or {}
    return {
        "generated_at": revalidation.get("generated_at"),
        "summary": {
            "watchlist_id": watchlist,
            "tickers": len(rows),
            "valuation_gate_improved": summary.get("valuation_gate_improved") or 0,
            "confirmed_order_count": sum(1 for row in revalidation.get("ticker_results") or [] if (row.get("confirmed_order_count") or 0) > 0),
            "tender_or_procurement_count": sum(row.get("tender_or_procurement_count") or 0 for row in revalidation.get("ticker_results") or []),
            "customer_capex_count": sum(row.get("customer_capex_count") or 0 for row in revalidation.get("ticker_results") or []),
            "proxy_strengthened": summary.get("proxy_strengthened") or 0,
            "new_reduced_size_pending": summary.get("new_reduced_size_pending") or 0,
            "primary_remaining_gates": {gate: len(tickers) for gate, tickers in distribution.items()},
        },
        "rows": rows,
        "remaining_valuation_blockers": blocker_rows[:50],
        "gate_distribution": {gate: tickers for gate, tickers in distribution.items()},
        "safety": revalidation.get("safety") or {},
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 22 Valuation / Demand Gate Summary",
        "",
        "## Overall",
        f"- Valuation gate improved: {summary.get('valuation_gate_improved')}",
        f"- Confirmed orders: {summary.get('confirmed_order_count')}",
        f"- Tender/procurement evidence: {summary.get('tender_or_procurement_count')}",
        f"- Customer capex evidence: {summary.get('customer_capex_count')}",
        f"- Proxy strengthened: {summary.get('proxy_strengthened')}",
        f"- New reduced-size pending: {summary.get('new_reduced_size_pending')}",
        "",
        "## By Ticker",
        "| Ticker | Valuation | Demand Evidence | Proxy | Promotion | Next Fix |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        demand = f"{row.get('demand_evidence')} / confirmed={row.get('confirmed_order')}"
        lines.append(
            f"| {row.get('ticker')} | {row.get('valuation_status')} | {demand} | "
            f"{row.get('proxy_status')} | {row.get('promotion_status')} | {row.get('next_fix')} |"
        )
    lines.extend(["", "## Remaining Valuation Blockers", "| Ticker | Blocker | Suggested Fix |", "|---|---|---|"])
    for row in payload.get("remaining_valuation_blockers") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('blocker')} | {row.get('suggested_fix')} |")
    return "\n".join(lines).rstrip() + "\n"


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    return compact_payload(build_revalidation(conn, parse_tickers(tickers, watchlist), watchlist=watchlist), watchlist)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 22 valuation/demand gate summary")
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
            entity_type="phase22_valuation_demand_gate_summary",
            entity_id=args.tickers or args.watchlist,
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
    log_run(SCRIPT_NAME, "success", "phase22 valuation/demand gate summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
