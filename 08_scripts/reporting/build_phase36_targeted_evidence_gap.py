#!/usr/bin/env python3
"""Build Phase 36 targeted evidence gap report."""

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
from smr_targeted_evidence_gap import build_targeted_evidence_gap

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_targeted_evidence_gap(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    body = payload.get("targeted_evidence_gap") or {}
    lines = [
        "# Phase 36 Targeted Evidence Gap",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Summary",
        f"- Research quality before: {body.get('research_quality_before')}",
        f"- Evidence coverage before: {body.get('evidence_coverage_before')}",
        f"- Research readiness: {body.get('research_readiness')}",
        f"- Semantic evidence total: {body.get('semantic_evidence_total')}",
        "",
        "## Critical Gaps",
        "| Variable | Status | Count | Impact | Confirmable | Why It Matters |",
        "|---|---|---:|---|---|---|",
    ]
    for row in body.get("critical_missing_variables") or []:
        lines.append(
            f"| {row.get('variable')} | {row.get('current_status')} | {row.get('current_evidence_count')} | "
            f"{row.get('impact_on_thesis')} | {row.get('can_be_confirmed_from_public_sources')} | {row.get('why_it_matters')} |"
        )
    lines.extend(["", "## Already Supported"])
    lines.extend(f"- {item}" for item in body.get("variables_already_supported") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 targeted evidence gap report")
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
