#!/usr/bin/env python3
"""Build Phase 41 follow-up dashboard."""

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

from build_phase41_customer_allocation_route import build_payload as build_customer_allocation
from build_phase41_official_consensus_availability import build_payload as build_official_consensus
from build_phase41_research_followup_queue import build_payload as build_queue
from build_phase41_supplier_share_route import build_payload as build_supplier_share
from smr_agents import DB_PATH
from smr_research_review_lifecycle import get_lifecycle_by_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    ticker = "300308.SZ"
    lifecycle = get_lifecycle_by_ticker(conn, ticker)
    queue = build_queue(conn, ticker)
    official = build_official_consensus(conn, ticker).get("official_consensus_availability") or {}
    supplier = build_supplier_share(conn, ticker).get("supplier_share_route") or {}
    customer = build_customer_allocation(conn, ticker).get("customer_allocation_route") or {}
    return {
        "generated_at": now_ts(),
        "summary": {
            "ticker": ticker,
            "review_status": lifecycle.get("research_review_status") or "unknown",
            "followup_queue_items": (queue.get("summary") or {}).get("followup_queue_items", 0),
            "official_consensus_status": official.get("status"),
            "supplier_share_status": supplier.get("status"),
            "customer_allocation_status": customer.get("status"),
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "next_steps": [
            "Check authorized consensus source availability",
            "Keep supplier share as scenario analysis unless directly disclosed",
            "Do not confirm customer allocation from proxy evidence",
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
    lines = ["# Phase 41 Follow-up Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {item}" for item in payload.get("next_steps") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 follow-up dashboard")
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
