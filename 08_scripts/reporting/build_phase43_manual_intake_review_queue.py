#!/usr/bin/env python3
"""Build Phase 43 manual intake candidate review queue."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_manual_intake_candidate_generator import build_candidate_generation_payload, list_manual_intake_candidates
from smr_manual_intake_permission_guard import build_permission_audit
from smr_manual_intake_rejection import list_rejection_records
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


FORBIDDEN_ACTIONS = [
    "confirm_supplier_share",
    "confirm_customer_allocation",
    "allow_promotion",
    "create_pending",
]

ALLOWED_ACTIONS = [
    "accept_as_candidate",
    "reject_manual_candidate",
    "downgrade_usage",
    "request_better_source",
]


def _candidate_rows(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    rows = list_manual_intake_candidates(conn, ticker=ticker)
    if rows:
        return rows
    generated = build_candidate_generation_payload(None, ticker=ticker, mode="dry_run")
    return (generated.get("manual_intake_candidate_generation") or {}).get("candidate_rows") or []


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    candidates = _candidate_rows(conn, ticker)
    audit_by_id = {
        row.get("candidate_id"): row
        for row in (build_permission_audit(conn, ticker).get("permission_audit") or {}).get("audit_rows") or []
    }
    items: list[dict[str, Any]] = []
    for candidate in candidates:
        audit = audit_by_id.get(candidate.get("candidate_id")) or {}
        review_reason = ["manual_source", "requires_human_review", "not_confirmed"]
        if audit.get("allowed_usage_downgraded"):
            review_reason.append("permission_downgraded")
        items.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "ticker": ticker,
                "evidence_type": candidate.get("evidence_type"),
                "source_type": candidate.get("source_type"),
                "confirmation_status": candidate.get("confirmation_status"),
                "allowed_usage": audit.get("final_allowed_usage") or candidate.get("allowed_usage"),
                "review_reason": review_reason,
                "recommended_action": "review_manual_candidate",
                "allowed_actions": list(ALLOWED_ACTIONS),
                "forbidden_actions": list(FORBIDDEN_ACTIONS),
                "pending_created": False,
                "promotion_allowed": False,
            }
        )
    rejections = list_rejection_records(conn, ticker=ticker)
    for record in rejections:
        items.append(
            {
                "rejection_id": record.get("rejection_id"),
                "ticker": ticker,
                "evidence_type": record.get("evidence_type"),
                "review_reason": ["manual_source", "rejected_input", "requires_fix"],
                "recommended_action": record.get("recommended_fix"),
                "allowed_actions": ["request_better_source"],
                "forbidden_actions": list(FORBIDDEN_ACTIONS),
                "pending_created": False,
                "promotion_allowed": False,
            }
        )
    types = Counter(item.get("evidence_type") for item in items)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_intake_review_queue": {
            "queue_items": len(items),
            "official_consensus_candidates": types.get("official_consensus", 0),
            "scenario_candidates": sum(1 for item in items if item.get("source_type") == "scenario_assumption"),
            "proxy_candidates": sum(1 for item in items if item.get("source_type") == "proxy_evidence_note"),
            "rejection_records": len(rejections),
            "items": items,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "review_queue_auto_approves": False,
            "accept_as_candidate_confirms_evidence": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("manual_intake_review_queue") or {}
    lines = [f"# Phase 43 Manual Intake Review Queue: {payload.get('ticker')}", "", "## Summary"]
    for key in ("queue_items", "official_consensus_candidates", "scenario_candidates", "proxy_candidates", "rejection_records"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Items"])
    for item in body.get("items") or []:
        label = item.get("candidate_id") or item.get("rejection_id")
        lines.append(f"- {label}: {item.get('recommended_action')}")
        lines.append(f"  Forbidden: {', '.join(item.get('forbidden_actions') or [])}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 manual intake review queue")
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
