#!/usr/bin/env python3
"""Build a Phase 14 thesis-aware daily summary."""

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
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase14_thesis_aware_daily_summary.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def latest_phase14_validation(conn: sqlite3.Connection, watchlist_id: str) -> dict[str, Any]:
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='task_registry_entry'"
    ).fetchone()
    if not table:
        return {}
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entry
        WHERE entity_type='phase14_thesis_aware_multi_ticker_live_validation'
          AND entity_id=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (watchlist_id,),
    ).fetchone()
    return loads_json(row[0], {}) if row else {}


def next_action_for(row: dict[str, Any]) -> str:
    if row.get("after_status") == "pending_human_review":
        return "human_review_required"
    if row.get("primary_thesis_type") == "unknown":
        return "manual_thesis_review_required"
    if row.get("core_blockers"):
        return "repair_core_blockers"
    if row.get("optional_warnings") or row.get("supporting_warnings"):
        return "track_non_core_warnings"
    return "continue_monitoring"


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticker": row.get("ticker"),
        "market": row.get("market"),
        "primary_thesis_type": row.get("primary_thesis_type"),
        "thesis_inference_confidence": row.get("thesis_inference_confidence"),
        "status": row.get("after_status") or row.get("status"),
        "promotion_mode": row.get("promotion_mode"),
        "action": row.get("action"),
        "position_policy": row.get("position_policy"),
        "suggested_position_pct": row.get("suggested_position_pct"),
        "core_blockers": row.get("core_blockers") or [],
        "supporting_warnings": row.get("supporting_warnings") or [],
        "optional_warnings": row.get("optional_warnings") or [],
        "data_quality_gate": row.get("data_quality_gate"),
        "bear_case_gate": row.get("bear_case_gate") or {},
        "portfolio_risk_status": row.get("portfolio_risk_status"),
        "decision_ledger_written": row.get("decision_ledger_written"),
        "next_action": next_action_for(row),
    }


def build_summary_payload(validation: dict[str, Any], watchlist_id: str) -> dict[str, Any]:
    rows = [compact_row(row) for row in validation.get("tickers") or []]
    pending = [row for row in rows if row.get("status") == "pending_human_review"]
    reduced = [row for row in pending if row.get("promotion_mode") == "reduced_size_pending"]
    shadow = [row for row in rows if row.get("status") == "candidate_shadow"]
    observation = [row for row in rows if row.get("status") == "observation_only"]
    unknown = [row for row in rows if row.get("primary_thesis_type") == "unknown"]
    core_blocker = [row for row in rows if row.get("core_blockers")]
    non_core_warning = [row for row in rows if row.get("supporting_warnings") or row.get("optional_warnings")]
    return {
        "generated_at": now_ts(),
        "watchlist_id": validation.get("watchlist_id") or watchlist_id,
        "run_id": validation.get("run_id"),
        "overall_result": (validation.get("summary") or {}).get("overall_result") or "skipped",
        "summary": {
            "pending_human_review": len(pending),
            "reduced_size_pending": len(reduced),
            "candidate_shadow": len(shadow),
            "observation_only": len(observation),
            "unknown_thesis": len(unknown),
            "core_blocker_tickers": [row.get("ticker") for row in core_blocker],
            "non_core_warning_tickers": [row.get("ticker") for row in non_core_warning],
        },
        "ticker_rows": rows,
        "pending_review": pending,
        "core_blockers": core_blocker,
        "non_core_warnings": non_core_warning,
        "unknown_thesis": unknown,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 14 Thesis-aware Daily Summary",
        "",
        "## Summary",
        f"- Pending human review: `{summary.get('pending_human_review') or 0}`",
        f"- Reduced-size pending: `{summary.get('reduced_size_pending') or 0}`",
        f"- Candidate shadow: `{summary.get('candidate_shadow') or 0}`",
        f"- Unknown thesis: `{summary.get('unknown_thesis') or 0}`",
        "",
        "## Pending Review",
        "| Ticker | Thesis | Action | Position | Warnings | Bear Case | Next Action |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in payload.get("pending_review") or []:
        warnings = ", ".join((row.get("supporting_warnings") or []) + (row.get("optional_warnings") or [])) or "-"
        bear = (row.get("bear_case_gate") or {}).get("overall_status") or "-"
        lines.append(
            f"| {row.get('ticker')} | {row.get('primary_thesis_type')} | {row.get('action')} | "
            f"{row.get('suggested_position_pct') or 0} | {warnings} | {bear} | {row.get('next_action')} |"
        )
    lines.extend([
        "",
        "## Core Blockers",
        "| Ticker | Thesis | Core Blockers | Required Fix |",
        "|---|---|---|---|",
    ])
    for row in payload.get("core_blockers") or []:
        blockers = ", ".join(row.get("core_blockers") or []) or "-"
        lines.append(f"| {row.get('ticker')} | {row.get('primary_thesis_type')} | {blockers} | repair core field evidence |")
    lines.extend([
        "",
        "## Non-core Warnings",
        "| Ticker | Thesis | Warnings | Impact |",
        "|---|---|---|---|",
    ])
    for row in payload.get("non_core_warnings") or []:
        warnings = ", ".join((row.get("supporting_warnings") or []) + (row.get("optional_warnings") or [])) or "-"
        lines.append(f"| {row.get('ticker')} | {row.get('primary_thesis_type')} | {warnings} | warning, not silent resolution |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 14 thesis-aware daily summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        validation = latest_phase14_validation(conn, args.watchlist)
        if validation:
            payload = build_summary_payload(validation, args.watchlist)
        else:
            payload = {
                "generated_at": now_ts(),
                "watchlist_id": args.watchlist,
                "overall_result": "skipped",
                "skip_reason": "no phase14 thesis-aware validation snapshot found",
                "summary": {},
                "ticker_rows": [],
            }
        output_dir = project_path("06_reports", "adhoc", "phase14")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_phase14_thesis_aware_daily_summary.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="phase14_thesis_aware_daily_summary",
            entity_id=args.watchlist,
            status=str(payload.get("overall_result") or "skipped"),
            source=SCRIPT_NAME,
            payload={**payload, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase14 thesis-aware daily summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
