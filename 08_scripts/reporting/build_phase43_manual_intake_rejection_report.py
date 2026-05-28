#!/usr/bin/env python3
"""Build Phase 43 manual intake rejection report."""

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
from smr_manual_intake_candidate_generator import build_candidate_generation_payload
from smr_manual_intake_rejection import list_rejection_records
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    persisted = list_rejection_records(conn, ticker=ticker)
    invalid_sample = build_candidate_generation_payload(None, ticker=ticker, sample="bad_consensus_internal_proxy", mode="dry_run")
    sample_rejections = (invalid_sample.get("manual_intake_candidate_generation") or {}).get("rejection_rows") or []
    records = persisted + [record for record in sample_rejections if record.get("rejection_id") not in {item.get("rejection_id") for item in persisted}]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_intake_rejection_report": {
            "persisted_rejection_records": len(persisted),
            "sample_rejection_records": len(sample_rejections),
            "rejection_records_total": len(records),
            "records": records,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "bad_input_silently_ignored": False,
            "rejection_deletes_payload": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("manual_intake_rejection_report") or {}
    lines = [f"# Phase 43 Manual Intake Rejection Report: {payload.get('ticker')}", "", "## Summary"]
    for key in ("persisted_rejection_records", "sample_rejection_records", "rejection_records_total"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Records"])
    for row in body.get("records") or []:
        lines.append(f"- {row.get('rejection_id')}: {', '.join(row.get('rejection_reasons') or [])}")
        lines.append(f"  Recommended fix: {row.get('recommended_fix')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 manual intake rejection report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
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
