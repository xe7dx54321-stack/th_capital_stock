#!/usr/bin/env python3
"""Build Phase 19 daily gate summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_promotion_block_reason import build_watchlist_block_diagnostics
from smr_registry import register_snapshot
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase19_daily_gate_summary.py"


def compact_payload(diag: dict, watchlist: str) -> dict:
    rows = []
    distribution: dict[str, list[str]] = defaultdict(list)
    for item in diag.get("ticker_results") or []:
        gate = item.get("primary_blocking_gate") or "UNKNOWN_GATE"
        distribution[gate].append(item.get("ticker"))
        rows.append(
            {
                "ticker": item.get("ticker"),
                "status": item.get("status"),
                "primary_thesis_type": item.get("primary_thesis_type"),
                "primary_blocking_gate": gate,
                "core_blockers": item.get("core_blockers") or [],
                "recovered_fields": item.get("recovered_fields") or [],
                "next_fix": (item.get("next_fix") or ["inspect remaining promotion metadata"])[0],
            }
        )
    summary = diag.get("summary") or {}
    return {
        "generated_at": diag.get("generated_at"),
        "summary": {
            "watchlist_id": watchlist,
            "tickers": len(rows),
            "pending_human_review": summary.get("pending_human_review") or 0,
            "candidate_shadow": summary.get("candidate_shadow") or 0,
            "observation_only": summary.get("observation_only") or 0,
            "core_blocker_count": summary.get("core_blocker_count") or 0,
            "primary_blocking_gates": {gate: len(tickers) for gate, tickers in distribution.items()},
        },
        "rows": rows,
        "gate_distribution": {gate: tickers for gate, tickers in distribution.items()},
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 19 Daily Gate Summary",
        "",
        "## Overall",
        f"- Pending: {summary.get('pending_human_review')}",
        f"- Candidate shadow: {summary.get('candidate_shadow')}",
        f"- Observation only: {summary.get('observation_only')}",
        f"- Core blocker count: {summary.get('core_blocker_count')}",
        f"- Main remaining gates: {json.dumps(summary.get('primary_blocking_gates') or {}, ensure_ascii=False)}",
        "",
        "## By Ticker",
        "| Ticker | Status | Thesis | Primary Gate | Recovered Fields | Next Fix |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('status')} | {row.get('primary_thesis_type')} | "
            f"{row.get('primary_blocking_gate')} | {', '.join(row.get('recovered_fields') or []) or '-'} | {row.get('next_fix')} |"
        )
    lines.extend(["", "## Remaining Gate Distribution", "| Gate | Count | Tickers |", "|---|---:|---|"])
    for gate, tickers in (payload.get("gate_distribution") or {}).items():
        lines.append(f"| {gate} | {len(tickers)} | {', '.join(tickers)} |")
    return "\n".join(lines).rstrip() + "\n"


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core") -> dict:
    return compact_payload(build_watchlist_block_diagnostics(conn, watchlist_id=watchlist), watchlist)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 19 daily gate summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase19_daily_gate_summary",
            entity_id=args.watchlist,
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase19 daily gate summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
