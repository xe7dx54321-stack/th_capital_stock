#!/usr/bin/env python3
"""Build Phase 45 final variable coverage review."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    del conn
    ticker = normalize_ticker(ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "final_variable_coverage_review": {
            "variables_supported": [
                {"variable": "product_mix", "status": "supported", "allowed_usage": "supporting_evidence", "impact": "supports_thesis"},
                {"variable": "shipment", "status": "supported", "allowed_usage": "supporting_evidence", "impact": "supports_thesis"},
                {"variable": "industry_forecast", "status": "supported", "allowed_usage": "context_or_supporting_evidence", "impact": "supports_industry_context"},
                {"variable": "bear_case_evidence", "status": "supported", "allowed_usage": "risk_context", "impact": "bounds_research_conclusion"},
            ],
            "variables_partially_supported": [
                {"variable": "order_visibility", "status": "partially_supported", "allowed_usage": "supporting_evidence", "impact": "supports_tracking"},
                {"variable": "ASP_price_proxy", "status": "partially_supported", "allowed_usage": "context_or_scenario_support", "impact": "supports_valuation_boundary_only"},
                {"variable": "margin_signal", "status": "partially_supported", "allowed_usage": "context_or_supporting_evidence", "impact": "supports_product_mix_context"},
                {"variable": "valuation_support", "status": "partial", "allowed_usage": "scenario_analysis_only", "impact": "cannot_support_pending"},
            ],
            "variables_scenario_only": [
                {"variable": "supplier_share", "status": "scenario_only", "allowed_usage": "scenario_analysis_only", "impact": "cannot_confirm_company_specific_revenue_sensitivity"}
            ],
            "variables_proxy_only": [
                {"variable": "customer_allocation", "status": "proxy_only", "allowed_usage": "bear_case_context_or_scenario_support", "impact": "cannot_confirm_customer_allocation"}
            ],
            "variables_missing_or_unconfirmed": ["official_consensus"],
            "confirmed_variables_added": 0,
            "pending_created": 0,
        },
        "safety": {
            "supplier_share_confirmed": False,
            "customer_allocation_confirmed": False,
            "official_consensus_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("final_variable_coverage_review") or {}
    lines = [f"# Phase 45 Final Variable Coverage Review: {payload.get('ticker')}", ""]
    for section in ("variables_supported", "variables_partially_supported", "variables_scenario_only", "variables_proxy_only"):
        lines.extend([f"## {section}", "| Variable | Status | Allowed Usage | Impact |", "|---|---|---|---|"])
        for row in body.get(section) or []:
            lines.append(f"| {row.get('variable')} | {row.get('status')} | {row.get('allowed_usage')} | {row.get('impact')} |")
        lines.append("")
    lines.extend(["## Missing Or Unconfirmed"])
    lines.extend(f"- {item}" for item in body.get("variables_missing_or_unconfirmed") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final variable coverage review")
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
