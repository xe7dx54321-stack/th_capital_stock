#!/usr/bin/env python3
"""Build a summary of recent live multi-ticker run history."""

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
from smr_live_run_history import ensure_live_run_history_tables, list_live_run_history
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase7_live_run_history_summary.py"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 7 Live Run History Summary",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- watchlist: `{payload.get('watchlist_id')}`",
        f"- run_count: `{payload.get('run_count')}`",
        f"- improved_ticker_total: `{payload.get('improved_ticker_total')}`",
        f"- worsened_ticker_total: `{payload.get('worsened_ticker_total')}`",
        f"- repeated_blocker_ticker_total: `{payload.get('repeated_blocker_ticker_total')}`",
        "",
        "## Runs",
        "",
        "| run_time | run_id | pending | candidate_shadow | observation | blocked | failed | changes |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for run in payload.get("runs") or []:
        changes = run.get("comparison") or {}
        lines.append(
            "| {run_time} | {run_id} | {pending} | {candidate_shadow} | {observation} | {blocked} | {failed} | +{improved}/-{worsened} / blockers={blockers} |".format(
                run_time=run.get("run_time") or "-",
                run_id=run.get("run_id") or "-",
                pending=run.get("pending_count") or 0,
                candidate_shadow=run.get("candidate_shadow_count") or 0,
                observation=run.get("observation_count") or 0,
                blocked=run.get("blocked_count") or 0,
                failed=run.get("failed_count") or 0,
                improved=len(changes.get("improved") or []),
                worsened=len(changes.get("worsened") or []),
                blockers=len(changes.get("repeated_blockers") or {}),
            )
        )
    lines.extend(["", "## Notable Changes", ""])
    for run in payload.get("runs") or []:
        changes = run.get("comparison") or {}
        improved = ", ".join(changes.get("improved") or []) or "-"
        worsened = ", ".join(changes.get("worsened") or []) or "-"
        blockers = changes.get("repeated_blockers") or {}
        blocker_text = "; ".join(f"{ticker}:{','.join(items)}" for ticker, items in blockers.items()) or "-"
        lines.append(f"- `{run.get('run_id')}` improved: {improved}; worsened: {worsened}; repeated_blockers: {blocker_text}")
    return "\n".join(lines).rstrip() + "\n"


def compact_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": row.get("run_id"),
        "run_time": row.get("run_time"),
        "watchlist_id": row.get("watchlist_id"),
        "ticker_count": row.get("ticker_count"),
        "pending_count": row.get("pending_count"),
        "candidate_shadow_count": row.get("candidate_shadow_count"),
        "observation_count": row.get("observation_count"),
        "blocked_count": row.get("blocked_count"),
        "failed_count": row.get("failed_count"),
        "comparison": row.get("comparison") or {},
        "summary": row.get("summary") or {},
        "per_ticker_status": row.get("per_ticker_status") or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Phase 7 live run history summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        ensure_live_run_history_tables(conn)
        runs = list_live_run_history(conn, watchlist_id=args.watchlist, limit=args.limit)
        payload = {
            "generated_at": now_ts(),
            "watchlist_id": args.watchlist,
            "run_count": len(runs),
            "runs": [compact_run(row) for row in runs],
            "improved_ticker_total": sum(len((row.get("comparison") or {}).get("improved") or []) for row in runs),
            "worsened_ticker_total": sum(len((row.get("comparison") or {}).get("worsened") or []) for row in runs),
            "repeated_blocker_ticker_total": sum(len((row.get("comparison") or {}).get("repeated_blockers") or {}) for row in runs),
        }
        output_dir = project_path("06_reports", "adhoc", "phase7")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_phase7_live_run_history_summary.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="phase7_live_run_history_summary",
            entity_id=payload["generated_at"][:10],
            status="generated",
            source=SCRIPT_NAME,
            payload={**payload, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase7 live run history summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
