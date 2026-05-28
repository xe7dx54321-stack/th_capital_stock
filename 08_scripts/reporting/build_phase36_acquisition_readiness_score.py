#!/usr/bin/env python3
"""Build Phase 36 acquisition readiness score."""

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
from smr_evidence_acquisition_readiness import build_acquisition_readiness_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_acquisition_readiness_score(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 36 Acquisition Readiness Score",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Summary",
        f"- Tasks scored: {summary.get('tasks_scored')}",
        f"- High priority: {summary.get('high_priority')}",
        f"- Manual or low confidence: {summary.get('manual_or_low_confidence')}",
        "",
        "| Task | Variable | Type | Score | Bucket | Reason |",
        "|---|---|---|---:|---|---|",
    ]
    for row in payload.get("acquisition_readiness") or []:
        lines.append(
            f"| {row.get('task_id')} | {row.get('variable')} | {row.get('task_type')} | "
            f"{row.get('readiness_score')} | {row.get('readiness_bucket')} | {row.get('reason')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 acquisition readiness score")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
