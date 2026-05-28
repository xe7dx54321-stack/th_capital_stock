#!/usr/bin/env python3
"""Build Phase 45 final thesis validity review."""

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
from smr_final_thesis_review import build_final_thesis_review
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_final_thesis_review(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("final_thesis_review") or {}
    lines = [f"# Phase 45 Final Thesis Review: {payload.get('ticker')}", ""]
    lines.extend(
        [
            "## Thesis",
            f"- primary_thesis: {body.get('primary_thesis')}",
            f"- thesis_status: {body.get('thesis_status')}",
            f"- thesis_confidence: {body.get('thesis_confidence')}",
            f"- conclusion_readiness: {body.get('conclusion_readiness')}",
            f"- investment_readiness: {body.get('investment_readiness')}",
            "",
            "## What Is Supported",
        ]
    )
    lines.extend(f"- {item}" for item in body.get("what_is_supported") or [])
    lines.extend(["", "## What Is Not Supported"])
    lines.extend(f"- {item}" for item in body.get("what_is_not_supported") or [])
    lines.extend(["", "## Boundaries", f"- scenario_dependency: {body.get('scenario_dependency')}", f"- valuation_boundary: {body.get('valuation_boundary')}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final thesis review")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
