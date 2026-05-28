#!/usr/bin/env python3
"""Build Phase 47 new evidence delta."""

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
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_new_evidence_delta_detector import build_new_evidence_delta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_new_evidence_delta(conn, ticker)


def render_markdown(payload: dict) -> str:
    delta = payload.get("new_evidence_delta") or {}
    lines = [
        f"# Phase 47 New Evidence Delta: {payload.get('ticker')}",
        "",
        f"- delta_status: {delta.get('delta_status')}",
        f"- new_evidence_found: {delta.get('new_evidence_found')}",
        f"- revalidation_required: {delta.get('revalidation_required')}",
        f"- evidence_count: {delta.get('evidence_count_before')}",
        f"- manual_candidates: {delta.get('manual_candidates_count')}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 new evidence delta")
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
