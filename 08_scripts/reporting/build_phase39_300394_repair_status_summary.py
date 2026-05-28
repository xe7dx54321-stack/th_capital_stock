#!/usr/bin/env python3
"""Build Phase 39 300394 repair status summary."""

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

from build_phase38_300394_repair_queue_summary import build_payload as build_phase38_repair
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REPAIR_CATEGORIES = [
    "SOURCE_INVENTORY_RECHECK",
    "TEXT_CACHE_REBUILD",
    "SEMANTIC_EXTRACTION_RERUN",
    "CANDIDATE_PERSISTENCE_RECHECK",
    "TICKER_MAPPING_RECHECK",
]


def build_payload(conn: sqlite3.Connection) -> dict:
    phase38 = build_phase38_repair(conn).get("repair_queue_summary") or {}
    actual = [
        (task.get("metadata") or {}).get("repair_task_type")
        for task in phase38.get("repair_tasks") or []
        if (task.get("metadata") or {}).get("repair_task_type")
    ]
    return {
        "generated_at": now_ts(),
        "ticker": "300394.SZ",
        "repair_status_summary": {
            "repair_tasks_total": phase38.get("repair_tasks_written", 0),
            "research_deepening_allowed": False,
            "current_status": "repair_required_before_research_deepening",
            "repair_categories": REPAIR_CATEGORIES,
            "phase38_repair_categories_present": sorted(set(actual)),
            "why_not_research_packet": [
                "evidence_chain_count remains 0",
                "semantic evidence not yet restored",
                "research quality remains low/thin",
            ],
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "research_packet_generated": False,
            "fake_evidence_written": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("repair_status_summary") or {}
    lines = [
        "# Phase 39 300394 Repair Status Summary",
        "",
        f"- Repair tasks total: {body.get('repair_tasks_total')}",
        f"- Current status: {body.get('current_status')}",
        f"- Research deepening allowed: {body.get('research_deepening_allowed')}",
        "",
        "## Repair Categories",
    ]
    lines.extend(f"- {item}" for item in body.get("repair_categories") or [])
    lines.extend(["", "## Why Not Research Packet"])
    lines.extend(f"- {item}" for item in body.get("why_not_research_packet") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 300394 repair status summary")
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
