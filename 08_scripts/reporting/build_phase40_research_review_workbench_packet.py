#!/usr/bin/env python3
"""Build Phase 40 research review workbench packet."""

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

from build_phase39_300308_evidence_contribution import build_payload as build_contribution
from build_phase39_300308_evidence_strengthened_packet import build_payload as build_strengthened_packet
from build_phase39_human_research_review_checklist import build_payload as build_checklist
from build_phase39_next_evidence_priority_update import build_payload as build_next_priority
from build_phase39_why_not_pending_reinforcement import build_payload as build_why_not_pending
from build_phase40_research_review_queue import build_payload as build_queue
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


EXPLICIT_NON_GOALS = [
    "Do not approve investment pending",
    "Do not create paper order",
    "Do not infer confirmed supplier share",
    "Do not infer confirmed customer allocation",
    "Do not treat internal proxy as official consensus",
    "Do not issue valuation targets or sizing guidance",
]


def build_payload(conn: sqlite3.Connection, ticker: str = "300308.SZ") -> dict:
    ticker = str(ticker or "300308.SZ").strip().upper()
    queue = build_queue(conn, ticker).get("items") or []
    item = queue[0] if queue else {}
    strengthened = build_strengthened_packet(conn).get("evidence_strengthened_packet") or {}
    contribution = build_contribution(conn).get("evidence_contribution") or {}
    checklist = build_checklist(conn, ticker).get("human_research_review_checklist") or {}
    why = build_why_not_pending(conn, ticker).get("why_not_pending_reinforcement") or {}
    priority = build_next_priority(conn, ticker).get("next_evidence_priority_update") or {}
    thesis = strengthened.get("thesis_update") or {}
    evidence_summary = {
        "evidence_before": strengthened.get("evidence_before"),
        "evidence_after": strengthened.get("evidence_after"),
        "new_evidence_count": strengthened.get("new_evidence_written"),
        "strengthened_variables": item.get("strengthened_variables") or contribution.get("variables_strengthened") or [],
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "research_review_workbench_packet": {
            "review_candidate_id": item.get("review_candidate_id"),
            "review_candidate_status": item.get("status") or "not_ready_for_research_review",
            "evidence_strengthened_summary": evidence_summary,
            "research_packet_summary": {
                "thesis": thesis.get("after"),
                "research_quality_delta": strengthened.get("quality_delta"),
                "confidence": item.get("confidence"),
            },
            "evidence_to_review": contribution.get("contribution_rows") or [],
            "human_checklist": checklist.get("checklist_items") or [],
            "why_not_pending": why.get("main_blockers") or [],
            "next_evidence_priority": priority.get("remaining_high_priority") or [],
            "allowed_review_actions": item.get("allowed_actions") or [],
            "explicit_non_goals": EXPLICIT_NON_GOALS,
            "promotion_boundary": {
                "pending_allowed": False,
                "paper_order_allowed": False,
                "promotion_allowed": False,
                "real_trade_allowed": False,
            },
        },
        "safety": {
            "packet_is_investment_memo": False,
            "pending_human_review_created": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("research_review_workbench_packet") or {}
    summary = body.get("evidence_strengthened_summary") or {}
    research = body.get("research_packet_summary") or {}
    lines = [
        f"# Phase 40 Research Review Workbench Packet: {payload.get('ticker')}",
        "",
        "## Review Status",
        f"- Status: {body.get('review_candidate_status')}",
        f"- Candidate ID: {body.get('review_candidate_id')}",
        "",
        "## What Changed",
        f"- Evidence before: {summary.get('evidence_before')}",
        f"- Evidence after: {summary.get('evidence_after')}",
        f"- New evidence count: {summary.get('new_evidence_count')}",
        "",
        "## Strengthened Variables",
    ]
    lines.extend(f"- {item}" for item in summary.get("strengthened_variables") or [])
    lines.extend(["", "## Evidence to Review"])
    for row in body.get("evidence_to_review") or []:
        lines.append(f"- {row.get('evidence_id')}: {row.get('variable')} / {row.get('contribution_type')}")
    lines.extend(["", "## Human Review Checklist"])
    for item in body.get("human_checklist") or []:
        lines.append(f"- {item.get('question')}")
    lines.extend(["", "## Why Not Pending"])
    for blocker in body.get("why_not_pending") or []:
        lines.append(f"- {blocker.get('blocker')}: {blocker.get('why_it_still_matters')}")
    lines.extend(["", "## Remaining Evidence Gaps"])
    for item in body.get("next_evidence_priority") or []:
        lines.append(f"- {item.get('variable')}: {item.get('recommended_mode')}")
    lines.extend(["", "## Allowed Research Actions"])
    lines.extend(f"- {item}" for item in body.get("allowed_review_actions") or [])
    lines.extend(["", "## Explicit Non-Goals"])
    lines.extend(f"- {item}" for item in body.get("explicit_non_goals") or [])
    lines.extend(["", "## Promotion Boundary"])
    boundary = body.get("promotion_boundary") or {}
    for key, value in boundary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Research Packet Summary", f"- Thesis: {research.get('thesis')}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 40 research review workbench packet")
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
