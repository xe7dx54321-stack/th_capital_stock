#!/usr/bin/env python3
"""Build Phase 45 final research packet."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase45_expectation_gap_valuation_boundary import build_payload as build_expectation
from build_phase45_final_bear_case_review import build_payload as build_bear
from build_phase45_final_evidence_sufficiency_review import build_payload as build_evidence
from build_phase45_final_research_asset_summary import build_payload as build_assets
from build_phase45_final_research_conclusion import build_payload as build_conclusion
from build_phase45_final_thesis_review import build_payload as build_thesis
from build_phase45_final_variable_coverage_review import build_payload as build_variables
from build_phase45_paper_watchlist_readiness_packet import build_payload as build_watchlist
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    assets = build_assets(conn, ticker).get("final_research_asset_summary") or {}
    thesis = build_thesis(conn, ticker).get("final_thesis_review") or {}
    evidence = build_evidence(conn, ticker).get("evidence_sufficiency_review") or {}
    variables = build_variables(conn, ticker).get("final_variable_coverage_review") or {}
    expectation = build_expectation(conn, ticker).get("expectation_gap_valuation_boundary") or {}
    bear = build_bear(conn, ticker).get("final_bear_case_review") or {}
    conclusion = build_conclusion(conn, ticker).get("final_research_conclusion") or {}
    watchlist = build_watchlist(conn, ticker).get("paper_watchlist_readiness_packet") or {}
    why_not_pending = {
        "pending_allowed": False,
        "reasons": conclusion.get("why_not_pending") or [],
        "hard_constraints": assets.get("remaining_core_gaps") or [],
    }
    next_tracking_plan = {
        "next_phase": "phase46_paper_watchlist_tracking",
        "tracking_variables": watchlist.get("tracking_variables") or [],
        "tracking_questions": watchlist.get("tracking_questions") or [],
        "watchlist_entry_created": False,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "final_research_packet": {
            "asset_summary": assets,
            "thesis_review": thesis,
            "evidence_sufficiency": evidence,
            "variable_coverage": variables,
            "expectation_gap_valuation_boundary": expectation,
            "bear_case_review": bear,
            "final_research_conclusion": conclusion,
            "paper_watchlist_readiness": watchlist,
            "why_not_pending": why_not_pending,
            "next_tracking_plan": next_tracking_plan,
            "promotion_boundary": {
                "pending_created": 0,
                "paper_order_created": 0,
                "real_trade_created": 0,
                "promotion_allowed_true": 0,
            },
        },
        "safety": {
            "packet_is_investment_memo": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    packet = payload.get("final_research_packet") or {}
    conclusion = packet.get("final_research_conclusion") or {}
    thesis = packet.get("thesis_review") or {}
    evidence = packet.get("evidence_sufficiency") or {}
    variables = packet.get("variable_coverage") or {}
    expectation = packet.get("expectation_gap_valuation_boundary") or {}
    bear = packet.get("bear_case_review") or {}
    watchlist = packet.get("paper_watchlist_readiness") or {}
    why = packet.get("why_not_pending") or {}
    tracking = packet.get("next_tracking_plan") or {}
    boundary = packet.get("promotion_boundary") or {}
    lines = [
        f"# Phase 45 Final Research Packet: {payload.get('ticker')}",
        "",
        "## Executive Research Conclusion",
        f"- conclusion_status: {conclusion.get('conclusion_status')}",
        f"- conclusion_confidence: {conclusion.get('conclusion_confidence')}",
        f"- paper_watchlist_readiness: {conclusion.get('paper_watchlist_readiness')}",
        "",
        "## Thesis Validity",
        f"- thesis_status: {thesis.get('thesis_status')}",
        f"- investment_readiness: {thesis.get('investment_readiness')}",
        "",
        "## Evidence Sufficiency",
        f"- research: {evidence.get('evidence_sufficiency_for_research_conclusion')}",
        f"- investment_pending: {evidence.get('evidence_sufficiency_for_investment_pending')}",
        "",
        "## Variable Coverage",
        f"- supported: {len(variables.get('variables_supported') or [])}",
        f"- scenario_only: {len(variables.get('variables_scenario_only') or [])}",
        f"- proxy_only: {len(variables.get('variables_proxy_only') or [])}",
        "",
        "## Expectation Gap & Valuation Boundary",
        f"- expectation_gap_status: {expectation.get('expectation_gap_status')}",
        f"- valuation_boundary: {expectation.get('valuation_boundary')}",
        "",
        "## Bear Case",
        f"- bear_case_status: {bear.get('bear_case_status')}",
        f"- residual_risk_level: {bear.get('residual_risk_level')}",
        "",
        "## Paper Watchlist Readiness",
        f"- readiness: {watchlist.get('readiness')}",
        f"- paper_order_allowed: {(watchlist.get('entry_boundary') or {}).get('paper_order_allowed')}",
        "",
        "## Why Not Pending",
    ]
    lines.extend(f"- {item}" for item in why.get("reasons") or [])
    lines.extend(["", "## Next Tracking Plan", f"- next_phase: {tracking.get('next_phase')}"])
    lines.extend(f"- {item}" for item in tracking.get("tracking_questions") or [])
    lines.extend(["", "## Promotion / Trading Boundary"])
    for key, value in boundary.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final research packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
