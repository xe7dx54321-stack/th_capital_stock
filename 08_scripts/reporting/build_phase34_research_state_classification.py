#!/usr/bin/env python3
"""Build Phase 34 ticker-level research state classification."""

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
from smr_research_state_classifier import build_research_state_classification

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    return build_research_state_classification(conn, ticker=ticker, tickers=tickers)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 34 Research State Classification",
        "",
        "## Overall",
        f"- Research strengthened: {summary.get('research_strengthened')}",
        f"- Research weakened: {summary.get('research_weakened')}",
        f"- Unchanged needs more data: {summary.get('unchanged_needs_more_data')}",
        f"- Ready for research packet: {summary.get('ready_for_research_packet')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Ticker",
        "| Ticker | State | Confidence | Reason | Next Step |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("ticker_results") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('research_state')} | {row.get('state_confidence')} | "
            f"{row.get('main_reason')} | {row.get('recommended_next_step')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 34 research state classification")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
