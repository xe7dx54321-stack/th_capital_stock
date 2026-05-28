#!/usr/bin/env python3
"""Build Phase 36 300394 evidence repair plan."""

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
from smr_evidence_chain_diagnostics import build_evidence_repair_plan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    return build_evidence_repair_plan(conn, "300394.SZ")


def render_markdown(payload: dict[str, Any]) -> str:
    plan = payload.get("evidence_repair_plan") or {}
    lines = [
        "# Phase 36 300394 Evidence Repair Plan",
        "",
        f"## Ticker\n{payload.get('ticker')}",
        "",
        "## Goal",
        f"- {plan.get('repair_goal')}",
        f"- Diagnostic status: {plan.get('diagnostic_status')}",
        "",
        "## Recommended Steps",
        "| Step | Task | Command Hint | Expected Result |",
        "|---:|---|---|---|",
    ]
    for step in plan.get("recommended_steps") or []:
        lines.append(
            f"| {step.get('step')} | {step.get('task')} | `{step.get('command_hint')}` | {step.get('expected_result')} |"
        )
    lines.extend(["", "## Do Not Do"])
    lines.extend(f"- {item}" for item in plan.get("do_not_do") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 300394 evidence repair plan")
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
