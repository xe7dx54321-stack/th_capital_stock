#!/usr/bin/env python3
"""Build Phase 42 fulfillment dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_followup_fulfillment_state import build_payload as build_state
from validate_phase42_research_packet_impact import build_payload as build_impact
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    ticker = "300308.SZ"
    state = build_state(conn, ticker).get("followup_fulfillment_state") or {}
    impact = build_impact(conn, ticker).get("research_packet_impact") or {}
    summary = {
        "ticker": ticker,
        "followup_requests": state.get("requests_total", 0),
        "fulfilled": state.get("fulfilled", 0),
        "authorized_source_required": state.get("authorized_source_required", 0),
        "scenario_only": state.get("scenario_only", 0),
        "proxy_only": state.get("proxy_only", 0),
        "official_consensus_added": bool(impact.get("official_consensus_added")),
        "supplier_share_confirmed": bool(impact.get("supplier_share_confirmed")),
        "customer_allocation_confirmed": bool(impact.get("customer_allocation_confirmed")),
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed_true": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "next_steps": [
            "User may provide authorized consensus source metadata",
            "Supplier share can only be used as explicit scenario assumption unless directly disclosed",
            "Customer allocation remains proxy-only unless direct disclosure appears",
        ],
        "safety": {
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    lines = ["# Phase 42 Fulfillment Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {item}" for item in payload.get("next_steps") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 fulfillment dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
