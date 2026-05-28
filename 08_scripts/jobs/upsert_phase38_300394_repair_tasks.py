#!/usr/bin/env python3
"""Upsert Phase 38 300394 evidence-chain repair tasks."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_blocker_repair_queue import list_repair_tasks, repair_id_for, upsert_repair_task
from smr_registry import register_snapshot
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


TARGET_TICKER = "300394.SZ"
WATCHLIST_ID = "supply_chain_pilot"

REPAIR_TASKS = [
    {
        "task_type": "SOURCE_INVENTORY_RECHECK",
        "blocker_code": "MISSING_SOURCE_EVIDENCE_ID",
        "priority": "high",
        "suggested_fix": "rerun real IR source inventory for 300394.SZ",
        "expected_impact": "restore source inventory traceability before evidence extraction",
    },
    {
        "task_type": "TEXT_CACHE_REBUILD",
        "blocker_code": "STALE_SOURCE_EVIDENCE",
        "priority": "high",
        "suggested_fix": "rebuild or restore text cache for known 300394.SZ IR sources",
        "expected_impact": "make body text available for quoted-span extraction",
    },
    {
        "task_type": "SEMANTIC_EXTRACTION_RERUN",
        "blocker_code": "LOW_DIRECTNESS_EVIDENCE",
        "priority": "medium",
        "suggested_fix": "rerun semantic extraction from restored text cache in dry-run first",
        "expected_impact": "create clean candidate rows only from body text",
    },
    {
        "task_type": "CANDIDATE_PERSISTENCE_RECHECK",
        "blocker_code": "EVIDENCE_QUALITY_LOW",
        "priority": "medium",
        "suggested_fix": "recheck quality/noise/sensitive guard before any candidate persistence",
        "expected_impact": "avoid fake or unsafe evidence-chain repair",
    },
    {
        "task_type": "GENERATED_STATE_MISSING",
        "blocker_code": "DATA_QUALITY_RISK",
        "priority": "medium",
        "suggested_fix": "verify ignored local generated state and DB availability before deepening research",
        "expected_impact": "separate missing local state from true absence of evidence",
    },
]


def _existing_phase38_tasks(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    tasks = list_repair_tasks(conn, ticker=TARGET_TICKER, watchlist_id=WATCHLIST_ID, limit=200)
    result = {}
    for task in tasks:
        metadata = task.get("metadata") or {}
        if metadata.get("phase") == 38 and metadata.get("repair_task_type"):
            result[str(metadata.get("repair_task_type"))] = task
    return result


def build_payload(conn: sqlite3.Connection, *, mode: str = "dry_run") -> dict[str, Any]:
    existing = _existing_phase38_tasks(conn)
    upserted: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    for task in REPAIR_TASKS:
        repair_id = repair_id_for(TARGET_TICKER, task["blocker_code"], WATCHLIST_ID)
        planned_row = {
            "repair_id": repair_id,
            "ticker": TARGET_TICKER,
            "task_type": task["task_type"],
            "blocker_code": task["blocker_code"],
            "priority": task["priority"],
            "suggested_fix": task["suggested_fix"],
            "expected_impact": task["expected_impact"],
        }
        planned.append(planned_row)
        if mode == "execute":
            upserted.append(
                upsert_repair_task(
                    conn,
                    ticker=TARGET_TICKER,
                    market="A",
                    watchlist_id=WATCHLIST_ID,
                    blocker_code=task["blocker_code"],
                    blocker_type="evidence_chain_repair",
                    priority=task["priority"],
                    severity="high" if task["priority"] == "high" else "medium",
                    fixability="medium",
                    expected_impact=task["expected_impact"],
                    suggested_fix=task["suggested_fix"],
                    source_run_ids=["phase37_300394_evidence_chain_repair"],
                    affected_fields=[task["task_type"]],
                    metadata={
                        "phase": 38,
                        "repair_task_type": task["task_type"],
                        "root_cause": "evidence_chain_zero_after_phase37_repair_dry_run",
                        "research_deepening_allowed": False,
                        "fake_evidence_written": False,
                        "promotion_rules_relaxed": False,
                    },
                )
            )
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "mode": mode,
        "repair_queue_upsert": {
            "repair_tasks_identified": len(REPAIR_TASKS),
            "repair_tasks_written": len(upserted) if mode == "execute" else 0,
            "duplicates_skipped": sum(1 for task in REPAIR_TASKS if task["task_type"] in existing),
            "planned_tasks": planned,
            "written_tasks": upserted,
            "research_deepening_allowed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "fake_evidence_written": False,
            "research_conclusion_generated": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert Phase 38 300394 repair tasks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase38_300394_repair_queue_upsert", TARGET_TICKER, mode, Path(__file__).name, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
