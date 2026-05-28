#!/usr/bin/env python3
"""Build Phase 35 research packet dashboard."""

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
from smr_phase25_utils import parse_tickers
from smr_research_quality_scoring import build_phase35_dashboard
from smr_single_stock_thesis_builder import PHASE35_PACKET_TICKERS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    selected = parse_tickers(tickers) if tickers else list(PHASE35_PACKET_TICKERS)
    return build_phase35_dashboard(conn, selected)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 35 Research Packet Dashboard",
        "",
        "## Summary",
        f"- Research packets: {summary.get('research_packets')}",
        f"- Research weakened: {summary.get('research_weakened')}",
        f"- Unchanged needs more data: {summary.get('unchanged_needs_more_data')}",
        f"- Ready for research packet: {summary.get('ready_for_research_packet')}",
        f"- New pending created: {summary.get('new_pending_created')}",
        f"- Paper order created: {summary.get('paper_order_created')}",
        "",
        "## Ticker Rows",
        "| Ticker | State | Quality | Coverage | Missing Variables | Next Step |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("ticker_rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('research_state')} | {row.get('research_quality')} | "
            f"{row.get('evidence_coverage')} | {', '.join(row.get('key_missing_variables') or [])} | {row.get('next_step')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 35 research packet dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
