#!/usr/bin/env python3
"""Build Phase 39 research-review candidate decision."""

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
from smr_research_review_candidate import build_research_review_candidate_decision

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_research_review_candidate_decision(conn, ticker)


def render_markdown(payload: dict) -> str:
    decision = payload.get("research_review_decision") or {}
    lines = [
        f"# Phase 39 Research Review Candidate Decision: {payload.get('ticker')}",
        "",
        f"- Decision: {decision.get('decision')}",
        f"- Confidence: {decision.get('confidence')}",
        "",
        "## Why Eligible",
    ]
    lines.extend(f"- {item}" for item in decision.get("why_eligible") or [])
    if decision.get("why_not_ready"):
        lines.extend(["", "## Why Not Ready"])
        lines.extend(f"- {item}" for item in decision.get("why_not_ready") or [])
    lines.extend(["", "## Why Not Pending"])
    lines.extend(f"- {item}" for item in decision.get("why_not_pending") or [])
    lines.extend(["", "## Human Review Questions"])
    lines.extend(f"- {item}" for item in decision.get("human_review_questions") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 39 research-review decision")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="300308.SZ")
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
