#!/usr/bin/env python3
"""Build Phase 24 CN tender/procurement summary."""

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
from smr_cn_tender_procurement import build_cn_tender_procurement_payload
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase24_cn_tender_procurement_summary.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [
            str(item.get("ticker") or "").upper()
            for item in load_watchlist_config(watchlist).get("tickers") or []
            if item.get("ticker") and str(item.get("ticker") or "").upper().endswith((".SZ", ".SH"))
        ]
    return []


def _best_strength(items: list[dict[str, Any]]) -> str:
    rank = {"blocked": 0, "context_only": 1, "weak_indication": 2, "medium_indication": 3, "strong_indication": 4, "near_confirmed": 5, "confirmed_award": 6}
    return max((item.get("evidence_strength") or "blocked" for item in items), key=lambda value: rank.get(str(value), 0), default="missing")


def build_ticker_summary(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    payload = build_cn_tender_procurement_payload(conn, ticker, execute=False)
    normalized = payload.get("normalized_results") or []
    candidates = payload.get("evidence_candidates") or []
    confirmed = [item for item in normalized if item.get("evidence_strength") == "confirmed_award"]
    indications = [item for item in normalized if item.get("evidence_strength") in {"near_confirmed", "strong_indication", "medium_indication"}]
    return {
        "ticker": payload.get("ticker"),
        "company_name": payload.get("company_name"),
        "queries_generated": payload.get("queries_generated"),
        "raw_results_found": payload.get("raw_results_found"),
        "normalized_items": payload.get("normalized_items"),
        "evidence_candidates": len(candidates),
        "best_evidence_strength": _best_strength(normalized),
        "confirmed_award_count": len(confirmed),
        "tender_or_procurement_indications": len(indications),
        "no_result_reason": payload.get("no_result_reason"),
        "next_fix": "need confirmed company-specific award or signed contract" if not confirmed else "review confirmed award source quality before promotion",
        "items": normalized[:10],
        "evidence_candidates_detail": candidates[:10],
    }


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict[str, Any]:
    rows = [build_ticker_summary(conn, ticker) for ticker in parse_tickers(tickers, watchlist)]
    all_candidates = [candidate for row in rows for candidate in row.get("evidence_candidates_detail") or []]
    payload = {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "queries_generated": sum(row.get("queries_generated") or 0 for row in rows),
            "raw_results_found": sum(row.get("raw_results_found") or 0 for row in rows),
            "normalized_items": sum(row.get("normalized_items") or 0 for row in rows),
            "confirmed_awards": sum(row.get("confirmed_award_count") or 0 for row in rows),
            "tender_or_procurement_indications": sum(row.get("tender_or_procurement_indications") or 0 for row in rows),
            "evidence_candidates": len(all_candidates),
            "connector_status": "partial",
        },
        "rows": rows,
        "evidence_candidates": all_candidates[:30],
        "safety": {
            "confirmed_award_fabricated": False,
            "news_mention_treated_as_confirmed": False,
            "raw_files_persisted": False,
            "promotion_rules_relaxed": False,
        },
    }
    if len(rows) == 1 and tickers:
        return {**rows[0], "generated_at": payload["generated_at"], "connector_status": "partial"}
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 24 CN Tender / Procurement Summary",
        "",
        "## Overall",
        f"- Tickers checked: {summary.get('tickers_checked')}",
        f"- Queries generated: {summary.get('queries_generated')}",
        f"- Raw results: {summary.get('raw_results_found')}",
        f"- Normalized items: {summary.get('normalized_items')}",
        f"- Confirmed awards: {summary.get('confirmed_awards')}",
        f"- Evidence candidates: {summary.get('evidence_candidates')}",
        f"- Connector status: {summary.get('connector_status')}",
        "",
        "## By Ticker",
        "| Ticker | Company | Results | Best Evidence | Confirmed Award | Next Fix |",
        "|---|---|---:|---|---:|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('company_name')} | {row.get('normalized_items')} | "
            f"{row.get('best_evidence_strength')} | {row.get('confirmed_award_count')} | {row.get('next_fix')} |"
        )
    lines.extend(["", "## Evidence Candidates", "| Ticker | Type | Strength | Source | Limitation |", "|---|---|---|---|---|"])
    for candidate in payload.get("evidence_candidates") or []:
        lines.append(
            f"| {candidate.get('ticker')} | {candidate.get('source_subtype')} | {candidate.get('evidence_strength')} | "
            f"{candidate.get('source_url')} | {'; '.join(candidate.get('limitations') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 24 tender/procurement summary")
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
            entity_type="phase24_tender_procurement_summary",
            entity_id=args.tickers or args.watchlist,
            status="built",
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
    log_run(SCRIPT_NAME, "success", "phase24 tender procurement summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
