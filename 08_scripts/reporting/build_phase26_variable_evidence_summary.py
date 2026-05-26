#!/usr/bin/env python3
"""Build Phase 26 supply-chain variable evidence summary."""

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
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers, unique_list
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase26_variable_evidence_summary.py"


def _row(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    packs = build_variable_evidence_packs(conn, ticker)
    gap = build_expectation_gap(conn, ticker, variable_evidence=packs).get("expectation_gap") or {}
    next_needs = unique_list([need for pack in packs.values() for need in (pack.get("next_connector_need") or [])])
    return {
        "ticker": ticker,
        "supplier_share": (packs.get("supplier_share") or {}).get("evidence_status"),
        "ASP_price_proxy": (packs.get("ASP_price_proxy") or {}).get("evidence_status"),
        "capacity": (packs.get("capacity") or {}).get("evidence_status"),
        "customer_allocation": (packs.get("customer_allocation_proxy") or {}).get("evidence_status"),
        "consensus": "official" if (packs.get("consensus") or {}).get("official_consensus_available") else "internal_proxy_only",
        "expectation_gap_confidence": gap.get("confidence"),
        "next_connector_need": next_needs[:6],
        "packs": packs,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    rows = [_row(conn, ticker) for ticker in resolved]
    all_packs = [pack for row in rows for pack in (row.get("packs") or {}).values()]
    summary = {
        "theme": "ai_optical_interconnect",
        "tickers_checked": len(rows),
        "variable_packs_generated": len(all_packs) + len(rows),
        "confirmed_variables": sum(1 for pack in all_packs if pack.get("evidence_status") == "confirmed"),
        "proxy_supported_variables": sum(1 for pack in all_packs if pack.get("evidence_status") == "proxy_supported"),
        "partial_variables": sum(1 for pack in all_packs if pack.get("evidence_status") == "partial"),
        "missing_variables": sum(1 for pack in all_packs if pack.get("evidence_status") == "missing"),
        "promotion_allowed_from_variable_evidence": 0,
    }
    key_missing = []
    for row in rows:
        for variable in ("supplier_share", "ASP_price_proxy", "customer_allocation"):
            if row.get(variable) in {"missing", "context_only", "partial"}:
                key_missing.append(
                    {
                        "ticker": row.get("ticker"),
                        "variable": variable,
                        "reason": "direct variable evidence unavailable",
                        "suggested_connector": ", ".join(row.get("next_connector_need") or []),
                    }
                )
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "rows": rows,
        "key_missing_variables": key_missing[:20],
        "safety": {
            "supplier_share_fabricated": False,
            "ASP_fabricated": False,
            "customer_allocation_fabricated": False,
            "internal_proxy_treated_as_official": False,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 26 Supply Chain Variable Evidence Summary",
        "",
        "## Overall",
        f"- Confirmed variables: {summary.get('confirmed_variables')}",
        f"- Proxy-supported variables: {summary.get('proxy_supported_variables')}",
        f"- Partial variables: {summary.get('partial_variables')}",
        f"- Missing variables: {summary.get('missing_variables')}",
        "",
        "## By Ticker",
        "| Ticker | Supplier Share | ASP | Capacity | Customer Allocation | Consensus | Gap Confidence | Next Connector |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('supplier_share')} | {row.get('ASP_price_proxy')} | "
            f"{row.get('capacity')} | {row.get('customer_allocation')} | {row.get('consensus')} | "
            f"{row.get('expectation_gap_confidence')} | {'; '.join(row.get('next_connector_need') or [])} |"
        )
    lines.extend(["", "## Key Missing Variables", "| Variable | Reason | Suggested Connector |", "|---|---|---|"])
    for item in payload.get("key_missing_variables") or []:
        lines.append(f"| {item.get('ticker')} {item.get('variable')} | {item.get('reason')} | {item.get('suggested_connector')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 26 variable evidence summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
        register_snapshot(conn, "phase26_variable_evidence_summary", args.tickers or "supply_chain_pilot", "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase26 variable evidence summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
