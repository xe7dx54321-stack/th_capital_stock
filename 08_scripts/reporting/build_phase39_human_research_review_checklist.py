#!/usr/bin/env python3
"""Build Phase 39 human research review checklist."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_contribution_analyzer import build_evidence_contribution
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _ids(rows: list[dict], variable: str) -> list[str]:
    return [str(row.get("evidence_id")) for row in rows if row.get("variable") == variable and row.get("evidence_id")]


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    contribution = build_evidence_contribution(conn, ticker).get("evidence_contribution") or {}
    rows = contribution.get("contribution_rows") or []
    missing = ["supplier_share", "official_consensus", "confirmed_customer_allocation"]
    return {
        "generated_at": now_ts(),
        "ticker": str(ticker or "").strip().upper(),
        "human_research_review_checklist": {
            "review_goal": "Decide whether the strengthened research packet deserves deeper manual research, not investment approval.",
            "checklist_items": [
                {
                    "question": "Does product mix evidence materially support high-end optical module exposure?",
                    "evidence_to_review": _ids(rows, "product_mix"),
                    "expected_human_judgment": "supportive / weak / irrelevant",
                },
                {
                    "question": "Does order visibility evidence reduce the main bear case?",
                    "evidence_to_review": _ids(rows, "order_visibility"),
                    "expected_human_judgment": "mitigates / unchanged / worsens",
                },
                {
                    "question": "Does shipment commentary add support without becoming a confirmed shipment number?",
                    "evidence_to_review": _ids(rows, "shipment"),
                    "expected_human_judgment": "supportive / context-only / irrelevant",
                },
                {
                    "question": "What exact evidence is still needed before investment pending?",
                    "evidence_gap": missing,
                },
            ],
            "explicit_non_goals": [
                "Do not approve investment pending",
                "Do not create paper order",
                "Do not infer confirmed supplier share",
                "Do not convert customer allocation proxy into confirmed allocation",
            ],
        },
        "safety": {
            "checklist_is_trade_review": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("human_research_review_checklist") or {}
    lines = [
        f"# Phase 39 Human Research Review Checklist: {payload.get('ticker')}",
        "",
        f"- Goal: {body.get('review_goal')}",
        "",
        "## Checklist",
    ]
    for item in body.get("checklist_items") or []:
        lines.append(f"- {item.get('question')}")
        if item.get("evidence_to_review"):
            lines.append(f"  Evidence: {', '.join(item.get('evidence_to_review') or [])}")
        if item.get("evidence_gap"):
            lines.append(f"  Evidence gap: {', '.join(item.get('evidence_gap') or [])}")
    lines.extend(["", "## Explicit Non-Goals"])
    lines.extend(f"- {item}" for item in body.get("explicit_non_goals") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 human research review checklist")
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
