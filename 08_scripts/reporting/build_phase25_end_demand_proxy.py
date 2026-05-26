#!/usr/bin/env python3
"""Build Phase 25 end-demand proxy report."""

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
from smr_end_demand_proxy import build_end_demand_proxy
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase25_end_demand_proxy.py"


def build_payload(conn: sqlite3.Connection, *, theme: str = "ai_optical_interconnect") -> dict[str, Any]:
    payload = build_end_demand_proxy(conn, theme)
    return {"generated_at": now_ts(), **payload}


def render_markdown(payload: dict[str, Any]) -> str:
    proxy = payload.get("end_demand_proxy") or {}
    lines = [
        "# Phase 25 End Demand Proxy",
        "",
        f"- Theme: {payload.get('theme')}",
        f"- Overall direction: {proxy.get('overall_direction')}",
        f"- Overall confidence: {proxy.get('overall_confidence')}",
        f"- Active evidence count: {proxy.get('active_evidence_count')}",
        "",
        "## Drivers",
        "| Driver | Direction | Confidence | Active Evidence | Limitation |",
        "|---|---|---|---:|---|",
    ]
    for driver in proxy.get("drivers") or []:
        lines.append(
            f"| {driver.get('driver')} | {driver.get('direction')} | {driver.get('confidence')} | "
            f"{len(driver.get('evidence_ids') or [])} | {'; '.join(driver.get('limitations') or [])} |"
        )
    lines.extend(["", "## Planned Sources", ""])
    for source in proxy.get("planned_sources") or []:
        lines.append(f"- {source}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 25 end-demand proxy")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--theme", default="ai_optical_interconnect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, theme=args.theme)
        register_snapshot(conn, "phase25_end_demand_proxy", args.theme, "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 end-demand proxy built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
