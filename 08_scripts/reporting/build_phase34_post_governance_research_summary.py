#!/usr/bin/env python3
"""Build Phase 34 post-governance research revalidation summary."""

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
from smr_post_governance_evidence_state import (
    build_bear_case_post_governance,
    build_expectation_gap_post_governance,
    build_next_evidence_plan,
    build_valuation_support_post_governance,
)
from smr_research_state_classifier import build_research_state_classification
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _by_ticker(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("ticker")): row for row in payload.get("ticker_results") or []}


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    states = build_research_state_classification(conn, ticker=ticker, tickers=tickers)
    gap = _by_ticker(build_expectation_gap_post_governance(conn, ticker=ticker, tickers=tickers))
    valuation = _by_ticker(build_valuation_support_post_governance(conn, ticker=ticker, tickers=tickers))
    bear = _by_ticker(build_bear_case_post_governance(conn, ticker=ticker, tickers=tickers))
    plan = _by_ticker(build_next_evidence_plan(conn, ticker=ticker, tickers=tickers))
    rows: list[dict[str, Any]] = []
    for row in states.get("ticker_results") or []:
        item = str(row.get("ticker"))
        plan_items = plan.get(item, {}).get("plan_items") or []
        top_missing = []
        for plan_item in plan_items:
            plan_type = str(plan_item.get("plan_type") or "")
            if plan_type.startswith("ASP"):
                top_missing.append("ASP_price_proxy")
            elif plan_type.startswith("SUPPLIER"):
                top_missing.append("supplier_share")
            elif plan_type.startswith("CUSTOMER"):
                top_missing.append("customer_allocation_proxy")
            elif plan_type.startswith("OFFICIAL"):
                top_missing.append("official_consensus")
        rows.append(
            {
                "ticker": item,
                "research_state": row.get("research_state"),
                "expectation_gap_delta": (gap.get(item) or {}).get("delta"),
                "valuation_support_delta": (valuation.get(item) or {}).get("delta"),
                "bear_case_delta": (bear.get(item) or {}).get("delta"),
                "top_missing_variables": list(dict.fromkeys(top_missing))[:4],
                "next_step": "targeted evidence plan",
            }
        )
    summary = dict(states.get("summary") or {})
    summary.update({"new_pending_created": 0, "paper_order_created": 0})
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "ticker_rows": rows,
        "safety": {
            "summary_is_trade_recommendation": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 34 Post-Governance Research Revalidation Summary",
        "",
        "## Overall",
        f"- Research strengthened: {summary.get('research_strengthened')}",
        f"- Research weakened: {summary.get('research_weakened')}",
        f"- Unchanged needs more data: {summary.get('unchanged_needs_more_data')}",
        f"- Ready for research packet: {summary.get('ready_for_research_packet')}",
        f"- New pending: {summary.get('new_pending_created')}",
        f"- Paper order: {summary.get('paper_order_created')}",
        "",
        "## By Ticker",
        "| Ticker | Research State | Gap Delta | Valuation Delta | Bear Delta | Missing Variables | Next Step |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("ticker_rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('research_state')} | {row.get('expectation_gap_delta')} | "
            f"{row.get('valuation_support_delta')} | {row.get('bear_case_delta')} | "
            f"{', '.join(row.get('top_missing_variables') or [])} | {row.get('next_step')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 34 post-governance research summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
