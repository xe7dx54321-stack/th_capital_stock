#!/usr/bin/env python3
"""Build Phase 42 follow-up fulfillment packet."""

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

from build_phase42_customer_allocation_proxy_audit import build_payload as build_customer_audit
from build_phase42_followup_fulfillment_state import build_payload as build_state
from build_phase42_official_consensus_fulfillment import build_payload as build_official
from build_phase42_supplier_share_scenario_registry import build_payload as build_supplier_scenario
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _status_map(state_payload: dict) -> dict:
    rows = (state_payload.get("followup_fulfillment_state") or {}).get("request_rows") or []
    return {row.get("request_type"): row for row in rows}


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    state = build_state(conn, ticker)
    statuses = _status_map(state)
    official = build_official(conn, ticker).get("official_consensus_fulfillment") or {}
    supplier_registry = build_supplier_scenario(conn, ticker).get("supplier_share_scenario_registry") or {}
    customer_audit = build_customer_audit(conn, ticker).get("customer_allocation_proxy_audit") or {}
    packet = {
        "official_consensus": {
            "fulfillment_status": official.get("fulfillment_status") or statuses.get("official_consensus", {}).get("status"),
            "fulfilled": False,
            "authorized_source_required": True,
        },
        "supplier_share": {
            "fulfillment_status": statuses.get("supplier_share", {}).get("status") or "scenario_only",
            "fulfilled": False,
            "scenario_registry_available": bool((supplier_registry.get("scenarios") or [])),
            "confirmed": False,
        },
        "confirmed_customer_allocation": {
            "fulfillment_status": statuses.get("confirmed_customer_allocation", {}).get("status") or "proxy_only",
            "fulfilled": False,
            "confirmed": False,
            "proxy_audit_violations": customer_audit.get("violations", 0),
        },
        "overall_fulfillment": "partial_or_open",
        "research_impact": "no_confirmed_variable_added",
        "pending_allowed": False,
        "paper_order_allowed": False,
        "promotion_allowed": False,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "followup_fulfillment_packet": packet,
        "safety": {
            "investment_memo_generated": False,
            "trade_recommendation_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("followup_fulfillment_packet") or {}
    lines = [
        f"# Phase 42 Follow-up Fulfillment Packet: {payload.get('ticker')}",
        "",
        "## Official Consensus",
        f"- Status: {(body.get('official_consensus') or {}).get('fulfillment_status')}",
        f"- Fulfilled: {(body.get('official_consensus') or {}).get('fulfilled')}",
        "",
        "## Supplier Share",
        f"- Status: {(body.get('supplier_share') or {}).get('fulfillment_status')}",
        f"- Scenario registry available: {(body.get('supplier_share') or {}).get('scenario_registry_available')}",
        "",
        "## Confirmed Customer Allocation",
        f"- Status: {(body.get('confirmed_customer_allocation') or {}).get('fulfillment_status')}",
        f"- Confirmed: {(body.get('confirmed_customer_allocation') or {}).get('confirmed')}",
        "",
        "## What Can Be Used",
        "- Authorized consensus metadata can be used only after validation.",
        "- Supplier share can be used only as explicit scenario assumption.",
        "- Customer allocation proxy can be used only as context or scenario support.",
        "",
        "## What Cannot Be Used",
        "- Internal proxy cannot fulfill official consensus.",
        "- Scenario assumption cannot become confirmed supplier share.",
        "- Customer proxy cannot become confirmed allocation.",
        "",
        "## Research Impact",
        f"- {body.get('research_impact')}",
        "",
        "## Pending Boundary",
        f"- pending_allowed: {body.get('pending_allowed')}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 follow-up fulfillment packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="300308.SZ")
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
