#!/usr/bin/env python3
"""Build Phase 38 300308 targeted candidate inventory."""

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
from smr_targeted_candidate_inventory import TARGET_TICKER, build_targeted_candidate_inventory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    return build_targeted_candidate_inventory(conn, TARGET_TICKER)


def render_markdown(payload: dict[str, Any]) -> str:
    inventory = payload.get("candidate_inventory") or {}
    lines = [
        "# Phase 38 300308 Candidate Inventory",
        "",
        f"- Ticker: {payload.get('ticker')}",
        f"- Candidates total: {inventory.get('candidates_total')}",
        "",
        "## By Variable",
    ]
    for variable, count in (inventory.get("by_variable") or {}).items():
        lines.append(f"- {variable}: {count}")
    lines.extend(["", "## Candidates", "| Candidate | Variable | Source Type | Usage | Warnings | Quote |", "|---|---|---|---|---|---|"])
    for row in inventory.get("candidates") or []:
        quote = " ".join(str(row.get("quoted_span") or "").split())[:160]
        warnings = ", ".join(row.get("warnings") or [])
        lines.append(
            f"| {row.get('candidate_id')} | {row.get('variable')} | {row.get('source_type')} | "
            f"{row.get('allowed_usage_suggestion')} | {warnings} | {quote} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 300308 candidate inventory")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
