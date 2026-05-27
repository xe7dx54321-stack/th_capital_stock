#!/usr/bin/env python3
"""Build Phase 33 lifecycle delta report from execute audit records."""

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
from smr_controlled_review_plan import phase33_audit_rows, phase33_audits, summarize_phase33_audit_deltas
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None) -> dict[str, Any]:
    audits = phase33_audits(conn, ticker=ticker)
    rows = phase33_audit_rows(audits)
    return {
        "generated_at": now_ts(),
        "summary": summarize_phase33_audit_deltas(audits),
        "rows": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 33 Evidence Lifecycle Delta Report",
        "",
        "## Summary",
        f"- Audit records: {summary.get('audit_records')}",
        f"- Approved evidence delta: {summary.get('approved_evidence_delta')}",
        f"- Rejected evidence delta: {summary.get('rejected_evidence_delta')}",
        f"- Downgraded evidence delta: {summary.get('downgraded_evidence_delta')}",
        f"- Marked noise delta: {summary.get('marked_noise_delta')}",
        f"- Needs better source delta: {summary.get('needs_better_source_delta')}",
        f"- Promotion allowed true delta: {summary.get('promotion_allowed_true_delta')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## Changes",
        "| Evidence | Ticker | Action | Before | After | Usage | Promotion |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        usage = f"{row.get('before_allowed_usage')} -> {row.get('after_allowed_usage')}"
        lines.append(
            f"| {row.get('evidence_id')} | {row.get('ticker')} | {row.get('action')} | {row.get('before_lifecycle_status')} | {row.get('after_lifecycle_status')} | {usage} | {row.get('promotion_allowed_after_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 33 lifecycle delta report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
