#!/usr/bin/env python3
"""Build Phase 34 research revalidation packet."""

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
from smr_phase25_utils import parse_tickers, resolve_phase25_tickers
from smr_post_governance_evidence_state import (
    build_bear_case_post_governance,
    build_expectation_gap_post_governance,
    build_next_evidence_plan,
    build_post_governance_evidence_state,
    build_valuation_support_post_governance,
    build_variable_pack_post_governance,
)
from smr_research_state_classifier import build_research_state_classification
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _index(rows: list[dict[str, Any]], key: str = "ticker") -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows}


def _single_packet(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, tickers=ticker)
    variables = build_variable_pack_post_governance(conn, tickers=ticker)
    gap = build_expectation_gap_post_governance(conn, tickers=ticker)
    valuation = build_valuation_support_post_governance(conn, tickers=ticker)
    bear = build_bear_case_post_governance(conn, tickers=ticker)
    states = build_research_state_classification(conn, tickers=ticker)
    plan = build_next_evidence_plan(conn, tickers=ticker)
    evidence_row = (evidence.get("ticker_results") or [{}])[0]
    state_row = (states.get("ticker_results") or [{}])[0]
    variable_row = (variables.get("ticker_results") or [{}])[0]
    gap_row = (gap.get("ticker_results") or [{}])[0]
    valuation_row = (valuation.get("ticker_results") or [{}])[0]
    bear_row = (bear.get("ticker_results") or [{}])[0]
    plan_row = (plan.get("ticker_results") or [{}])[0]
    return {
        "ticker": ticker,
        "company_name": evidence_row.get("company_name"),
        "research_revalidation_packet": {
            "research_state": state_row.get("research_state"),
            "state_confidence": state_row.get("state_confidence"),
            "evidence_state": evidence_row.get("evidence_state") or {},
            "variable_pack_delta": variable_row.get("variable_pack_delta") or [],
            "expectation_gap_delta": gap_row,
            "valuation_support_delta": valuation_row,
            "bear_case_delta": bear_row,
            "key_positive_factors": state_row.get("positive_factors") or [],
            "key_negative_factors": state_row.get("negative_factors") or [],
            "next_evidence_plan": plan_row.get("plan_items") or [],
            "promotion_status": {
                "new_pending_created": False,
                "promotion_allowed": False,
                "reason": "research revalidation only",
            },
        },
    }


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    selected = [ticker] if ticker else (parse_tickers(tickers) if tickers else resolve_phase25_tickers(None))
    packets = [_single_packet(conn, item) for item in selected]
    if len(packets) == 1 and ticker:
        return {**packets[0], "generated_at": now_ts()}
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(packets),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "packets": packets,
        "safety": {
            "research_revalidation_is_trade_advice": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    packet = payload if payload.get("research_revalidation_packet") else (payload.get("packets") or [{}])[0]
    body = packet.get("research_revalidation_packet") or {}
    lines = [
        "# Phase 34 Research Revalidation Packet",
        "",
        f"## Ticker\n{packet.get('ticker')} / {packet.get('company_name')}",
        "",
        f"## Research State\n{body.get('research_state')} ({body.get('state_confidence')})",
        "",
        "## What Improved",
        *[f"- {item}" for item in body.get("key_positive_factors") or []],
        "",
        "## What Weakened",
        *[f"- {item}" for item in body.get("key_negative_factors") or []],
        "",
        "## What Stayed Unchanged",
        "- Promotion remains blocked; this packet is research revalidation only.",
        "",
        "## Key Missing Variables",
    ]
    for item in body.get("key_negative_factors") or []:
        if "missing" in str(item):
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Expectation Gap",
            f"- Delta: {(body.get('expectation_gap_delta') or {}).get('delta')}",
            "",
            "## Valuation Support",
            f"- Delta: {(body.get('valuation_support_delta') or {}).get('delta')}",
            "",
            "## Bear Case",
            f"- Delta: {(body.get('bear_case_delta') or {}).get('delta')}",
            "",
            "## Next Evidence Plan",
        ]
    )
    for item in body.get("next_evidence_plan") or []:
        lines.append(f"- {item.get('plan_type')}: {item.get('reason')}")
    promotion = body.get("promotion_status") or {}
    lines.extend(
        [
            "",
            "## Promotion Boundary",
            f"- Promotion allowed: {promotion.get('promotion_allowed')}",
            f"- New pending created: {promotion.get('new_pending_created')}",
            f"- Reason: {promotion.get('reason')}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 34 research revalidation packet")
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
