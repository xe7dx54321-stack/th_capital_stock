#!/usr/bin/env python3
"""Build Phase 45 final research conclusion."""

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
from smr_final_research_conclusion import build_final_research_conclusion
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    return build_final_research_conclusion(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("final_research_conclusion") or {}
    lines = [f"# Phase 45 Final Research Conclusion: {payload.get('ticker')}", ""]
    for key in ("conclusion_status", "conclusion_confidence", "paper_watchlist_readiness", "allowed_next_step"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Why"])
    lines.extend(f"- {item}" for item in body.get("why") or [])
    lines.extend(["", "## Why Not Pending"])
    lines.extend(f"- {item}" for item in body.get("why_not_pending") or [])
    lines.extend(["", "## Forbidden Next Steps"])
    lines.extend(f"- {item}" for item in body.get("forbidden_next_steps") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final research conclusion")
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
