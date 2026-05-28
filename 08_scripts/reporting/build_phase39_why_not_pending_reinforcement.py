#!/usr/bin/env python3
"""Build Phase 39 why-not-pending reinforcement."""

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

from build_phase39_research_review_candidate_decision import build_payload as build_decision
from smr_agents import DB_PATH
from smr_evidence_contribution_analyzer import build_evidence_contribution
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


MAIN_BLOCKERS = [
    {
        "blocker": "supplier_share_unconfirmed",
        "why_it_still_matters": "Without supplier share, company-specific revenue sensitivity remains scenario-only.",
    },
    {
        "blocker": "official_consensus_missing",
        "why_it_still_matters": "Without official consensus, expectation gap cannot be benchmarked reliably.",
    },
    {
        "blocker": "confirmed_customer_allocation_missing",
        "why_it_still_matters": "Customer allocation proxy remains insufficient for investment promotion.",
    },
]


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    decision = build_decision(conn, ticker).get("research_review_decision") or {}
    contribution = build_evidence_contribution(conn, ticker).get("evidence_contribution") or {}
    return {
        "generated_at": now_ts(),
        "ticker": str(ticker or "").strip().upper(),
        "why_not_pending_reinforcement": {
            "research_review_candidate": decision.get("decision") == "research_review_candidate",
            "pending_allowed": False,
            "main_blockers": MAIN_BLOCKERS,
            "what_improved_but_not_enough": contribution.get("variables_strengthened") or [],
            "promotion_boundary": {
                "promotion_allowed": False,
                "paper_order_allowed": False,
                "real_trade_allowed": False,
            },
        },
        "safety": {
            "missing_variables_weakened": False,
            "trade_recommendation_generated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("why_not_pending_reinforcement") or {}
    lines = [
        f"# Phase 39 Why-Not-Pending Reinforcement: {payload.get('ticker')}",
        "",
        f"- Research review candidate: {body.get('research_review_candidate')}",
        f"- Pending allowed: {body.get('pending_allowed')}",
        "",
        "## Main Blockers",
    ]
    for blocker in body.get("main_blockers") or []:
        lines.append(f"- {blocker.get('blocker')}: {blocker.get('why_it_still_matters')}")
    lines.extend(["", "## Improved But Not Enough"])
    lines.extend(f"- {item}" for item in body.get("what_improved_but_not_enough") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 why-not-pending reinforcement")
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
