#!/usr/bin/env python3
"""Build Phase 35 variable coverage matrix."""

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
from smr_research_quality_scoring import build_variable_coverage_matrix

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_variable_coverage_matrix(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 35 Variable Coverage Matrix",
        "",
        f"## Ticker\n{payload.get('ticker')}",
        "",
        "| Variable | Status | Evidence Count | Usage | Impact |",
        "|---|---|---:|---|---|",
    ]
    for row in payload.get("variable_matrix") or []:
        lines.append(
            f"| {row.get('variable')} | {row.get('status')} | {row.get('evidence_count')} | "
            f"{row.get('allowed_usage')} | {row.get('impact_on_thesis')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 variable coverage matrix")
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
