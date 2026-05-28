#!/usr/bin/env python3
"""Build Phase 43 manual intake candidate dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, JOBS_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_candidates import build_payload as build_candidates
from persist_phase43_manual_intake_candidates import build_payload as build_persistence
from validate_phase43_manual_intake_research_impact import build_payload as build_impact
from smr_agents import DB_PATH
from smr_manual_intake_rejection import list_rejection_records
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    ticker = "300308.SZ"
    candidates = build_candidates(conn, ticker=ticker, mode="dry_run").get("manual_intake_candidate_generation") or {}
    persistence = build_persistence(conn, ticker=ticker, mode="dry_run").get("manual_intake_persistence") or {}
    impact = build_impact(conn, ticker).get("manual_intake_research_impact") or {}
    rejections = [row for row in list_rejection_records(conn, ticker=ticker) if row.get("intake_id", "").endswith("_bad_consensus_proxy") is False]
    summary = {
        "ticker": ticker,
        "payloads_checked": candidates.get("payloads_checked", 0),
        "candidates_created": candidates.get("candidates_created", 0),
        "candidates_written": impact.get("manual_candidates_written") or persistence.get("candidates_available", 0),
        "rejections": len(rejections),
        "official_consensus_candidate_added": bool(impact.get("official_consensus_candidate_added")),
        "official_consensus_confirmed": False,
        "supplier_share_scenario_added": bool(impact.get("supplier_share_scenario_added")),
        "supplier_share_confirmed": False,
        "customer_allocation_proxy_added": bool(impact.get("customer_allocation_proxy_added")),
        "customer_allocation_confirmed": False,
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed_true": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "safety": {
            "candidate_is_confirmed_evidence": False,
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
    lines = ["# Phase 43 Manual Intake Candidate Dashboard", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Boundary",
            "- candidates remain candidates, not confirmed evidence",
            "- supplier share remains scenario-only",
            "- customer allocation remains proxy-only",
            "- no pending review, paper order, promotion, or real trade path is created",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 manual intake dashboard")
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
