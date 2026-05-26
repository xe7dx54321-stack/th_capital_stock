#!/usr/bin/env python3
"""Build Phase 25 supply-chain expectation-gap summary dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase25_supply_chain_expectation_gap_packet import build_packet
from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers, unique_list
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase25_supply_chain_gap_summary.py"


def _row_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    sections = packet.get("sections") or {}
    gap = sections.get("expectation_gap") or {}
    uncertainties = gap.get("key_uncertainties") or []
    needs = sections.get("next_connector_needs") or []
    return {
        "ticker": packet.get("ticker"),
        "company_name": packet.get("company_name"),
        "expectation_gap_status": gap.get("status"),
        "score": gap.get("score"),
        "confidence": gap.get("confidence"),
        "key_uncertainties": uncertainties[:5],
        "next_connector_need": " / ".join(needs[:3]),
        "promotion_allowed": packet.get("promotion_allowed"),
    }


def build_payload(conn: sqlite3.Connection, *, watchlist: str | None = "supply_chain_pilot", tickers: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers, watchlist)
    packets = [build_packet(conn, ticker) for ticker in resolved]
    rows = [_row_from_packet(packet) for packet in packets]
    positive = {"strong_positive_gap", "potential_positive_gap"}
    next_needs = unique_list([need for packet in packets for need in ((packet.get("sections") or {}).get("next_connector_needs") or [])])
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "theme": "ai_optical_interconnect",
            "tickers_checked": len(rows),
            "positive_gap_candidates": sum(1 for row in rows if row.get("expectation_gap_status") in positive),
            "insufficient_data": sum(1 for row in rows if row.get("expectation_gap_status") == "insufficient_data"),
            "conflicted": sum(1 for row in rows if row.get("expectation_gap_status") == "conflicted"),
            "new_pending_created": 0,
        },
        "rows": rows,
        "next_connector_needs": [{"need": need, "reason": "missing variable or planned source required for higher confidence"} for need in next_needs],
        "safety": {
            "promotion_rules_relaxed": False,
            "expectation_gap_direct_pending": False,
            "real_trading_risk": False,
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 25 Supply Chain Expectation Gap Summary",
        "",
        "## Overall",
        f"- Theme: {summary.get('theme')}",
        f"- Positive gap candidates: {summary.get('positive_gap_candidates')}",
        f"- Insufficient data: {summary.get('insufficient_data')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Ticker",
        "| Ticker | Company | Gap Status | Score | Confidence | Key Uncertainty | Next Connector |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('company_name')} | {row.get('expectation_gap_status')} | "
            f"{row.get('score')} | {row.get('confidence')} | {'; '.join(row.get('key_uncertainties') or [])} | {row.get('next_connector_need')} |"
        )
    lines.extend(["", "## Next Connector Needs", "| Need | Reason |", "|---|---|"])
    for item in payload.get("next_connector_needs") or []:
        lines.append(f"| {item.get('need')} | {item.get('reason')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 25 supply-chain gap summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="supply_chain_pilot")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, tickers=args.tickers)
        register_snapshot(conn, "phase25_supply_chain_gap_summary", args.tickers or args.watchlist, "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 supply-chain gap summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
