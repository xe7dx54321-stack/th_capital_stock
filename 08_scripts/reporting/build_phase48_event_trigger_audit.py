#!/usr/bin/env python3
"""Build Phase 48 event trigger audit report."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path: sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_event_trigger_audit import list_event_trigger_audits
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn, ticker):
    records = list_event_trigger_audits(conn, ticker)
    return {
        "generated_at": now_ts(), "ticker": ticker,
        "audit_records": len(records), "audit_rows": records,
        "safety": {
            "pending_in_audit": all(not r.get("pending_created") for r in records),
            "order_in_audit": all(not r.get("paper_order_created") for r in records),
            "trade_in_audit": all(not r.get("real_trade_created") for r in records),
        },
    }

def render_markdown(payload):
    lines = [f"# Phase 48 Event Trigger Audit: {payload.get('ticker')}", "",
             f"- audit_records: {payload.get('audit_records')}"]
    for r in payload.get("audit_rows") or []:
        lines.append(f"- {r.get('action')}: {r.get('before_watchlist_status')} -> {r.get('after_watchlist_status')}")
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event trigger audit")
    p.add_argument("--db-path", default=str(DB_PATH)); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    conn = sqlite3.connect(args.db_path)
    try: payload = build_payload(conn, args.ticker)
    finally: conn.close()
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
