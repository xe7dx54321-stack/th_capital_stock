#!/usr/bin/env python3
"""Build Phase 39 review decision dashboard."""

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

from build_phase39_300394_repair_status_summary import build_payload as build_repair_status
from build_phase39_research_review_candidate_decision import build_payload as build_decision
from build_phase39_why_not_pending_reinforcement import build_payload as build_why_not_pending
from validate_phase38_300308_research_packet_post_persistence import build_payload as build_revalidation
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    decision = build_decision(conn, "300308.SZ").get("research_review_decision") or {}
    revalidation = build_revalidation(conn).get("research_packet_post_persistence") or {}
    why = build_why_not_pending(conn, "300308.SZ").get("why_not_pending_reinforcement") or {}
    repair = build_repair_status(conn).get("repair_status_summary") or {}
    return {
        "generated_at": now_ts(),
        "summary": {
            "300308_decision": decision.get("decision"),
            "300308_research_quality_delta": revalidation.get("quality_delta"),
            "300308_pending_allowed": why.get("pending_allowed"),
            "300394_status": repair.get("current_status"),
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "ticker_rows": [
            {
                "ticker": "300308.SZ",
                "status": decision.get("decision"),
                "next_step": "manual research review checklist",
                "why_not_pending": [item.get("blocker") for item in why.get("main_blockers") or []],
            },
            {
                "ticker": "300394.SZ",
                "status": repair.get("current_status"),
                "next_step": "repair source/text/semantic chain",
            },
        ],
        "safety": {
            "dashboard_is_investment_advice": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 39 Review Decision Dashboard",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Ticker Rows", "| Ticker | Status | Next Step |", "|---|---|---|"])
    for row in payload.get("ticker_rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('status')} | {row.get('next_step')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 review decision dashboard")
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
