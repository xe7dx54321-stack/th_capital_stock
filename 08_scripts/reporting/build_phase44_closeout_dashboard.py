#!/usr/bin/env python3
"""Build Phase 44 closeout dashboard."""

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

from build_phase44_manual_candidate_closeout_packet import build_payload as build_packet
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    ticker = "300308.SZ"
    packet = build_packet(conn, ticker).get("manual_candidate_closeout_packet") or {}
    matrix = packet.get("final_usage_matrix") or {}
    summary = {
        "ticker": ticker,
        "manual_candidates_reviewed": packet.get("manual_candidates_reviewed", 0),
        "audit_records": packet.get("audit_records", 0),
        "confirmed_variables_added": matrix.get("confirmed_variables_added", 0),
        "usable_for_promotion_true": matrix.get("usable_for_promotion_true", 0),
        "pending_created": 0,
        "paper_order_created": 0,
        "manual_intake_branch_status": packet.get("manual_intake_branch_status"),
        "next_mainline_step": packet.get("next_mainline_step"),
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
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
    lines = ["# Phase 44 Closeout Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 44 closeout dashboard")
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
