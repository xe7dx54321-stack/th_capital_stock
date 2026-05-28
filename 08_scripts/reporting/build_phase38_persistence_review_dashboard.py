#!/usr/bin/env python3
"""Build Phase 38 persistence and review dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_candidate_quality_review import build_payload as build_quality_review
from build_phase38_300308_evidence_chain_refresh import build_payload as build_chain_refresh
from build_phase38_300308_targeted_review_queue import build_payload as build_review_queue
from build_phase38_300394_repair_queue_summary import build_payload as build_repair_summary
from validate_phase38_300308_research_packet_post_persistence import build_payload as build_revalidation
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    quality = build_quality_review(conn).get("candidate_quality_review") or {}
    queue = build_review_queue(conn).get("targeted_review_queue") or {}
    refresh = build_chain_refresh(conn).get("evidence_chain_refresh") or {}
    revalidation = build_revalidation(conn).get("research_packet_post_persistence") or {}
    repair = build_repair_summary(conn).get("repair_queue_summary") or {}
    return {
        "generated_at": now_ts(),
        "summary": {
            "300308_candidates_total": quality.get("candidates_reviewed", 0),
            "eligible_for_persistence": quality.get("eligible_for_persistence", 0),
            "candidates_written": refresh.get("new_candidates_written", 0),
            "review_queue_items": queue.get("queue_items", 0),
            "evidence_after": refresh.get("evidence_after", 0),
            "research_quality_delta": revalidation.get("quality_delta"),
            "300394_repair_tasks_written": repair.get("repair_tasks_written", 0),
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "ticker_rows": [
            {
                "ticker": "300308.SZ",
                "mode": "candidate_review_and_guarded_persistence",
                "status": revalidation.get("quality_delta"),
                "why_not_pending": "supplier share, official consensus, and confirmed customer allocation still missing",
            },
            {
                "ticker": "300394.SZ",
                "mode": "repair_queue_hardening",
                "status": f"{repair.get('repair_tasks_written', 0)} repair tasks written",
                "why_not_pending": "research deepening disabled until evidence chain is repaired",
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


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 38 Persistence & Review Dashboard",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Tickers", "| Ticker | Mode | Status | Boundary |", "|---|---|---|---|"])
    for row in payload.get("ticker_rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('mode')} | {row.get('status')} | {row.get('why_not_pending')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 persistence/review dashboard")
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
