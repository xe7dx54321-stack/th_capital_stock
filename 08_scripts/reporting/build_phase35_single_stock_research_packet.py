#!/usr/bin/env python3
"""Build Phase 35 single-stock research packet."""

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
    build_valuation_support_post_governance,
)
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_quality_scoring import (
    build_research_quality_score,
    build_research_scenarios,
    build_safe_next_evidence_plan,
    build_variable_coverage_matrix,
    build_why_not_pending,
)
from smr_single_stock_thesis_builder import build_single_stock_thesis
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _first_row(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("ticker_results") or []
    return dict(rows[0]) if rows else {}


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    thesis_payload = build_single_stock_thesis(conn, ticker)
    evidence_payload = build_research_evidence_chain(conn, ticker)
    matrix_payload = build_variable_coverage_matrix(conn, ticker)
    quality_payload = build_research_quality_score(conn, ticker)
    scenarios_payload = build_research_scenarios(conn, ticker)
    why_payload = build_why_not_pending(conn, ticker)
    next_plan = build_safe_next_evidence_plan(conn, ticker)
    expectation = _first_row(build_expectation_gap_post_governance(conn, tickers=ticker))
    valuation = _first_row(build_valuation_support_post_governance(conn, tickers=ticker))
    bear = _first_row(build_bear_case_post_governance(conn, tickers=ticker))
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "company_name": thesis_payload.get("company_name"),
        "single_stock_research_packet": {
            "research_thesis": thesis_payload.get("research_thesis") or {},
            "evidence_chain": evidence_payload.get("evidence_chain") or {},
            "variable_matrix": matrix_payload.get("variable_matrix") or [],
            "expectation_gap": expectation,
            "valuation_support": valuation,
            "bear_case": bear,
            "research_quality": quality_payload.get("research_quality") or {},
            "research_scenarios": scenarios_payload.get("research_scenarios") or {},
            "why_not_pending": why_payload.get("why_not_pending") or {},
            "next_evidence_plan": next_plan.get("plan_items") or [],
            "promotion_boundary": {
                "promotion_allowed": False,
                "new_pending_created": False,
                "paper_order_created": False,
                "reason": "Phase 35 research packet only",
            },
        },
        "safety": {
            "packet_is_investment_memo": False,
            "trade_recommendation_generated": False,
            "position_sizing_generated": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    packet = payload.get("single_stock_research_packet") or {}
    thesis = packet.get("research_thesis") or {}
    chain = packet.get("evidence_chain") or {}
    quality = packet.get("research_quality") or {}
    why = packet.get("why_not_pending") or {}
    boundary = packet.get("promotion_boundary") or {}
    lines = [
        "# Single-Stock Research Packet",
        "",
        f"## Ticker / Company\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Research Thesis",
        f"- Confidence: {thesis.get('thesis_confidence')}",
        f"- State: {thesis.get('research_state')}",
        f"- Summary: {thesis.get('thesis_summary')}",
        "",
        "## Evidence Chain",
        f"- Total evidence: {chain.get('total_evidence')}",
        f"- Reviewed evidence: {chain.get('reviewed_evidence')}",
        f"- Approved evidence: {chain.get('approved_evidence')}",
        f"- Downgraded evidence: {chain.get('downgraded_evidence')}",
        "",
        "## Variable Coverage",
        "| Variable | Status | Evidence Count | Impact |",
        "|---|---|---:|---|",
    ]
    for row in packet.get("variable_matrix") or []:
        lines.append(f"| {row.get('variable')} | {row.get('status')} | {row.get('evidence_count')} | {row.get('impact_on_thesis')} |")
    lines.extend(
        [
            "",
            "## Expectation Gap",
            f"- Delta: {(packet.get('expectation_gap') or {}).get('delta')}",
            "",
            "## Valuation Support",
            f"- Delta: {(packet.get('valuation_support') or {}).get('delta')}",
            "",
            "## Bear Case",
            f"- Delta: {(packet.get('bear_case') or {}).get('delta')}",
            "",
            "## Research Quality",
            f"- Overall quality: {quality.get('overall_quality')}",
            f"- Evidence coverage: {quality.get('evidence_coverage')}",
            f"- Research readiness: {quality.get('research_readiness')}",
            "",
            "## Bull / Base / Bear Scenario",
        ]
    )
    for key in ("bull_case", "base_case", "bear_case"):
        item = (packet.get("research_scenarios") or {}).get(key) or {}
        lines.append(f"- {key}: {item.get('description')}")
    lines.extend(["", "## Why Not Pending"])
    lines.extend(f"- {item}" for item in why.get("core_reasons") or [])
    lines.extend(["", "## Next Evidence Plan"])
    for item in packet.get("next_evidence_plan") or []:
        lines.append(f"- {item.get('plan_type')}: {item.get('reason')}")
    lines.extend(
        [
            "",
            "## Promotion Boundary",
            f"- Promotion allowed: {boundary.get('promotion_allowed')}",
            f"- New pending created: {boundary.get('new_pending_created')}",
            f"- Paper order created: {boundary.get('paper_order_created')}",
            f"- Reason: {boundary.get('reason')}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 single-stock research packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
