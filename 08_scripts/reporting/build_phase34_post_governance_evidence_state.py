#!/usr/bin/env python3
"""Build Phase 34 post-governance evidence state report."""

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
from smr_post_governance_evidence_state import build_post_governance_evidence_state

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    return build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 34 Post-Governance Evidence State",
        "",
        "## Summary",
        f"- Tickers checked: {summary.get('tickers_checked')}",
        f"- Reviewed evidence: {summary.get('reviewed_evidence')}",
        f"- Approved evidence: {summary.get('approved_evidence')}",
        f"- Rejected evidence: {summary.get('rejected_evidence')}",
        f"- Downgraded evidence: {summary.get('downgraded_evidence')}",
        f"- Marked noise: {summary.get('marked_noise')}",
        f"- Needs better source: {summary.get('needs_better_source')}",
        f"- Repair tasks open: {summary.get('repair_tasks_open')}",
        "",
        "## By Ticker",
        "| Ticker | Reviewed | Approved | Rejected | Downgraded | Noise | Better Source | Strengthened | Weakened | Core Gaps |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in payload.get("ticker_results") or []:
        state = row.get("evidence_state") or {}
        delta = row.get("evidence_delta") or {}
        lines.append(
            f"| {row.get('ticker')} | {state.get('reviewed_evidence')} | {state.get('approved_evidence')} | "
            f"{state.get('rejected_evidence')} | {state.get('downgraded_evidence')} | {state.get('marked_noise')} | "
            f"{state.get('needs_better_source')} | {', '.join(delta.get('strengthened_variables') or [])} | "
            f"{', '.join(delta.get('weakened_variables') or [])} | {', '.join(row.get('remaining_core_gaps') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 34 post-governance evidence state")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
