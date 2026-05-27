#!/usr/bin/env python3
"""Build Phase 31 evidence review audit report."""

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
from smr_evidence_review_audit import list_evidence_review_audits, summarize_audits
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, evidence_id: str | None = None) -> dict:
    audits = list_evidence_review_audits(conn, ticker=ticker, evidence_id=evidence_id)
    summary = summarize_audits(audits)
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "audits": audits,
        "safety": {
            "promotion_allowed_after_action_true": summary.get("promotion_allowed_true", 0),
            "raw_source_text_recorded": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 31 Evidence Review Audit Report",
        "",
        "## Overall",
        f"- Audit records: {summary.get('audit_records')}",
        f"- Execute actions: {summary.get('execute_actions')}",
        f"- Dry-run actions: {summary.get('dry_run_actions')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        "",
        "## Audit Records",
        "| Created At | Evidence | Action | Before | After | Promotion Allowed |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("audits") or []:
        lines.append(
            f"| {row.get('created_at')} | {row.get('evidence_id')} | {row.get('action')} | {row.get('before_status')} | {row.get('after_status')} | {row.get('promotion_allowed_after_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 31 evidence review audit report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--evidence-id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, evidence_id=args.evidence_id)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
