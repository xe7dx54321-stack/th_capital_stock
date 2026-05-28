#!/usr/bin/env python3
"""Build Phase 42 supplier-share scenario registry."""

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
from smr_supplier_share_scenario_registry import build_supplier_share_scenario_registry

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_supplier_share_scenario_registry(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("supplier_share_scenario_registry") or {}
    lines = [f"# Phase 42 Supplier Share Scenario Registry: {payload.get('ticker')}", ""]
    for scenario in body.get("scenarios") or []:
        lines.append(f"- {scenario.get('scenario_id')}: {scenario.get('allowed_usage')} / confirmed={scenario.get('is_confirmed')}")
        lines.append(f"  Caveats: {', '.join(scenario.get('caveats') or [])}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 supplier-share scenario registry")
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
