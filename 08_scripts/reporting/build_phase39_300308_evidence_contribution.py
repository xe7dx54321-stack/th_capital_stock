#!/usr/bin/env python3
"""Build Phase 39 300308 evidence contribution report."""

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
from smr_evidence_contribution_analyzer import TARGET_TICKER, build_evidence_contribution

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    return build_evidence_contribution(conn, TARGET_TICKER)


def render_markdown(payload: dict) -> str:
    body = payload.get("evidence_contribution") or {}
    lines = [
        "# Phase 39 Evidence Contribution: 300308.SZ",
        "",
        f"- New evidence count: {body.get('new_evidence_count')}",
        f"- Variables strengthened: {', '.join(body.get('variables_strengthened') or [])}",
        "",
        "## Contribution Rows",
    ]
    for row in body.get("contribution_rows") or []:
        lines.extend(
            [
                f"- Evidence: {row.get('evidence_id')}",
                f"  Variable: {row.get('variable')}",
                f"  Contribution: {row.get('contribution_type')}",
                f"  Supports: {', '.join(row.get('what_it_supports') or [])}",
                f"  Does not support: {', '.join(row.get('what_it_does_not_support') or [])}",
            ]
        )
    lines.extend(["", "## Summary Judgment", str(body.get("summary_judgment") or "")])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 300308 evidence contribution")
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
