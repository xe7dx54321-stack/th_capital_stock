#!/usr/bin/env python3
"""Build Phase 35 why-not-pending explainer."""

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
from smr_research_quality_scoring import build_why_not_pending

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_why_not_pending(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    body = payload.get("why_not_pending") or {}
    lines = [
        "# Phase 35 Why Not Pending",
        "",
        f"## Ticker\n{payload.get('ticker')}",
        "",
        "## Boundary",
        f"- Promotion allowed: {body.get('promotion_allowed')}",
        "",
        "## Core Reasons",
    ]
    lines.extend(f"- {item}" for item in body.get("core_reasons") or [])
    lines.extend(["", "## Secondary Reasons"])
    lines.extend(f"- {item}" for item in body.get("secondary_reasons") or [])
    lines.extend(["", "## What Would Need To Change"])
    lines.extend(f"- {item}" for item in body.get("what_would_need_to_change") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 why-not-pending explainer")
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
