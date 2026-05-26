#!/usr/bin/env python3
"""Build Phase 20 daily research gate summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_registry import register_snapshot
from smr_runlog import log_run
from validate_phase20_promotion_revalidation import build_payload as build_revalidation

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase20_research_gate_summary.py"


def _main_gate(row: dict) -> str:
    if row.get("thesis_status_after") == "metadata_only_candidate":
        return "THESIS_CONFIDENCE_GATE"
    if row.get("bear_case_status_after") in {"requires_more_evidence", "unresolved_core"}:
        return "BEAR_CASE_GATE"
    if row.get("valuation_status_after") in {"blocked", "insufficient", "context_only"}:
        return "VALUATION_GATE"
    if row.get("proxy_status_after") in {"weak", "missing", "invalid", "conflicted"}:
        return "PROXY_SIGNAL_GATE"
    if row.get("after_status") == "pending_human_review":
        return "REVIEW_STATE_GATE"
    return row.get("primary_gate_before") or "UNKNOWN_GATE"


def compact_payload(revalidation: dict, watchlist: str) -> dict:
    distribution: dict[str, list[str]] = defaultdict(list)
    improvement_tickers: dict[str, list[str]] = defaultdict(list)
    rows = []
    reduced = 0
    for item in revalidation.get("ticker_results") or []:
        gate = _main_gate(item)
        distribution[gate].append(item.get("ticker"))
        changed = " ".join(item.get("why_changed") or []).lower()
        if "bear_case_gate" in changed:
            improvement_tickers["bear_case"].append(item.get("ticker"))
        if "valuation gate" in changed:
            improvement_tickers["valuation"].append(item.get("ticker"))
        if "proxy gate" in changed:
            improvement_tickers["proxy"].append(item.get("ticker"))
        if "thesis evidence" in changed:
            improvement_tickers["thesis_evidence"].append(item.get("ticker"))
        if item.get("promotion_mode") == "reduced_size_pending":
            reduced += 1
        rows.append(
            {
                "ticker": item.get("ticker"),
                "status": item.get("after_status"),
                "primary_gate": gate,
                "bear_case_status": item.get("bear_case_status_after"),
                "valuation_status": item.get("valuation_status_after"),
                "proxy_status": item.get("proxy_status_after"),
                "thesis_status": item.get("thesis_status_after"),
                "next_fix": (item.get("why_no_pending") or ["inspect remaining gate metadata"])[0],
            }
        )
    summary = revalidation.get("summary") or {}
    return {
        "generated_at": revalidation.get("generated_at"),
        "summary": {
            "watchlist_id": watchlist,
            "tickers": len(rows),
            "pending_human_review": sum(1 for row in rows if row.get("status") == "pending_human_review"),
            "reduced_size_pending": reduced,
            "candidate_shadow": sum(1 for row in rows if row.get("status") == "candidate_shadow"),
            "observation_only": sum(1 for row in rows if row.get("status") == "observation_only"),
            "primary_blocking_gates": {gate: len(tickers) for gate, tickers in distribution.items()},
            "gate_improvements": {
                "bear_case": summary.get("bear_case_gate_improved") or 0,
                "valuation": summary.get("valuation_gate_improved") or 0,
                "proxy": summary.get("proxy_gate_improved") or 0,
                "thesis_evidence": summary.get("thesis_evidence_improved") or 0,
            },
        },
        "rows": rows,
        "gate_distribution": {gate: tickers for gate, tickers in distribution.items()},
        "improvement_tickers": {gate: tickers for gate, tickers in improvement_tickers.items()},
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 20 Research Gate Summary",
        "",
        "## Overall",
        f"- Pending: {summary.get('pending_human_review')}",
        f"- Reduced-size pending: {summary.get('reduced_size_pending')}",
        f"- Candidate shadow: {summary.get('candidate_shadow')}",
        f"- Main blocking gates: {json.dumps(summary.get('primary_blocking_gates') or {}, ensure_ascii=False)}",
        "",
        "## Gate Improvements",
        "| Gate | Improved Count | Tickers |",
        "|---|---:|---|",
    ]
    improvements = summary.get("gate_improvements") or {}
    for gate, count in improvements.items():
        tickers = (payload.get("improvement_tickers") or {}).get(gate) or []
        lines.append(f"| {gate} | {count} | {', '.join(tickers) or '-'} |")
    lines.extend(["", "## By Ticker", "| Ticker | Status | Main Gate | Bear Case | Valuation | Proxy | Next Fix |", "|---|---|---|---|---|---|---|"])
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('status')} | {row.get('primary_gate')} | "
            f"{row.get('bear_case_status')} | {row.get('valuation_status')} | {row.get('proxy_status')} | {row.get('next_fix')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_tickers(raw: str | None, watchlist: str) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    from smr_phase6_watchlists import load_watchlist_config

    return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    return compact_payload(build_revalidation(conn, parse_tickers(tickers, watchlist), watchlist=watchlist), watchlist)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 20 research gate summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase20_research_gate_summary",
            entity_id=args.watchlist,
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase20 research gate summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
