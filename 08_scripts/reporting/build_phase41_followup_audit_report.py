#!/usr/bin/env python3
"""Build Phase 41 follow-up audit report."""

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
from smr_research_followup_audit import list_followup_audit_records
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str | None = None) -> dict:
    records = list_followup_audit_records(conn, ticker=ticker)
    return {
        "generated_at": now_ts(),
        "followup_audit_report": {
            "audit_records": len(records),
            "pending_created": sum(1 for row in records if row.get("pending_created")),
            "paper_order_created": sum(1 for row in records if row.get("paper_order_created")),
            "promotion_allowed_true": sum(1 for row in records if row.get("promotion_allowed")),
            "records": records,
        },
        "safety": {
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("followup_audit_report") or {}
    lines = [
        "# Phase 41 Follow-up Audit Report",
        "",
        f"- Audit records: {body.get('audit_records')}",
        f"- Pending created: {body.get('pending_created')}",
        f"- Paper order created: {body.get('paper_order_created')}",
        "",
        "## Records",
    ]
    for row in body.get("records") or []:
        lines.append(f"- {row.get('created_at')} / {row.get('ticker')} / {row.get('evidence_type')}: {row.get('before_status')} -> {row.get('after_status')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 follow-up audit report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
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
