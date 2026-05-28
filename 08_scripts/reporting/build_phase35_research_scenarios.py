#!/usr/bin/env python3
"""Build Phase 35 research scenarios."""

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
from smr_research_quality_scoring import build_research_scenarios

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return build_research_scenarios(conn, ticker)


def render_markdown(payload: dict[str, Any]) -> str:
    scenarios = payload.get("research_scenarios") or {}
    lines = [
        "# Phase 35 Bull / Base / Bear Research Scenarios",
        "",
        f"## Ticker\n{payload.get('ticker')}",
    ]
    for key, title in (("bull_case", "Bull Case"), ("base_case", "Base Case"), ("bear_case", "Bear Case")):
        item = scenarios.get(key) or {}
        lines.extend(["", f"## {title}", f"- Description: {item.get('description')}"])
        if item.get("required_missing_variables"):
            lines.append(f"- Required missing variables: {', '.join(item.get('required_missing_variables') or [])}")
        if item.get("current_support_level"):
            lines.append(f"- Current support level: {item.get('current_support_level')}")
        if item.get("current_bear_strength"):
            lines.append(f"- Current bear strength: {item.get('current_bear_strength')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 research scenarios")
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
