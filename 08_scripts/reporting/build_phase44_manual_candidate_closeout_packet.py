#!/usr/bin/env python3
"""Build Phase 44 manual candidate closeout packet."""

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

from build_phase44_manual_candidate_final_usage_matrix import build_payload as build_matrix
from build_phase44_manual_candidate_review_audit import build_payload as build_audit
from validate_phase44_manual_candidate_research_impact_closeout import build_payload as build_impact
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    audit = build_audit(conn, ticker).get("manual_candidate_review_audit") or {}
    matrix = build_matrix(conn, ticker).get("manual_candidate_final_usage_matrix") or {}
    impact = build_impact(conn, ticker).get("manual_candidate_research_impact_closeout") or {}
    actions = list(dict.fromkeys(row.get("action") for row in audit.get("records") or [] if row.get("action")))
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_candidate_closeout_packet": {
            "manual_candidates_reviewed": impact.get("manual_candidates_reviewed", 0),
            "actions_executed": actions,
            "audit_records": audit.get("audit_records", 0),
            "final_usage_matrix": matrix,
            "research_impact": {
                "research_quality_delta": impact.get("research_quality_delta"),
                "expectation_gap_delta": impact.get("expectation_gap_delta"),
                "pending_created": 0,
                "paper_order_created": 0,
                "promotion_allowed_true": 0,
            },
            "manual_intake_branch_status": "closed" if impact.get("manual_candidates_reviewed") == 3 else "open",
            "next_mainline_step": "phase45_final_research_packet_review",
        },
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
    body = payload.get("manual_candidate_closeout_packet") or {}
    lines = [f"# Phase 44 Manual Candidate Review Closeout: {payload.get('ticker')}", ""]
    lines.extend(["## Reviewed Candidates", f"- manual_candidates_reviewed: {body.get('manual_candidates_reviewed')}"])
    lines.extend(["", "## Actions Executed"])
    lines.extend(f"- {action}" for action in body.get("actions_executed") or [])
    lines.extend(["", "## Final Usage Matrix"])
    for row in ((body.get("final_usage_matrix") or {}).get("rows") or []):
        lines.append(f"- {row.get('candidate_type')}: {row.get('review_status')} / {row.get('final_allowed_usage')}")
    impact = body.get("research_impact") or {}
    lines.extend(["", "## Research Impact", f"- research_quality_delta: {impact.get('research_quality_delta')}", f"- pending_created: {impact.get('pending_created')}"])
    lines.extend(["", "## Why Not Pending", "- no confirmed variables were added", "- manual candidates remain promotion-disabled"])
    lines.extend(["", "## Manual Intake Branch Status", f"- {body.get('manual_intake_branch_status')}"])
    lines.extend(["", "## Next Mainline Step", f"- {body.get('next_mainline_step')}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 44 closeout packet")
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
