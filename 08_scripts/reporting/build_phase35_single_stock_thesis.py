#!/usr/bin/env python3
"""Build Phase 35 single-stock research thesis."""

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
from smr_single_stock_thesis_builder import build_single_stock_thesis

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_single_stock_thesis(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    thesis = payload.get("research_thesis") or {}
    lines = [
        "# Phase 35 Single-Stock Research Thesis",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Thesis",
        f"- Theme: {thesis.get('primary_theme')}",
        f"- Type: {thesis.get('thesis_type')}",
        f"- Confidence: {thesis.get('thesis_confidence')}",
        f"- State: {thesis.get('research_state')}",
        f"- Summary: {thesis.get('thesis_summary')}",
        "",
        "## Positive Drivers",
    ]
    lines.extend(f"- {item}" for item in thesis.get("positive_drivers") or [])
    lines.extend(["", "## Negative Drivers"])
    lines.extend(f"- {item}" for item in thesis.get("negative_drivers") or [])
    boundary = thesis.get("promotion_boundary") or {}
    lines.extend(
        [
            "",
            "## Promotion Boundary",
            f"- Promotion allowed: {boundary.get('promotion_allowed')}",
            f"- New pending created: {boundary.get('new_pending_created')}",
            f"- Paper order created: {boundary.get('paper_order_created')}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 single-stock thesis")
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
