#!/usr/bin/env python3
"""Build Phase 32 review action audit summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_review_audit import list_evidence_review_audits
from smr_sensitive_variable_guard import is_sensitive_variable
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, evidence_id: str | None = None) -> dict[str, Any]:
    audits = list_evidence_review_audits(conn, ticker=ticker, evidence_id=evidence_id)
    actions = Counter(row.get("action") for row in audits)
    sensitive_confirmed = 0
    for row in audits:
        metadata = row.get("metadata") or {}
        guard = metadata.get("sensitive_guard") or {}
        if guard.get("blocked_confirmed_upgrade") or (is_sensitive_variable(guard.get("variable_type")) and str(row.get("after_status")) == "confirmed"):
            sensitive_confirmed += 1
    return {
        "generated_at": now_ts(),
        "summary": {
            "audit_records": len(audits),
            "actions_by_type": dict(actions),
            "promotion_allowed_after_action_true": sum(1 for row in audits if row.get("promotion_allowed_after_action")),
            "sensitive_variable_confirmed_upgrades": sensitive_confirmed,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "recent_actions": audits[:20],
        "safety": {
            "audit_records_zero_allowed": True,
            "raw_source_text_recorded": False,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 32 Review Action Audit Summary",
        "",
        "## Overall",
        f"- Audit records: {summary.get('audit_records')}",
        f"- Promotion allowed after action true: {summary.get('promotion_allowed_after_action_true')}",
        f"- Sensitive variable confirmed upgrades: {summary.get('sensitive_variable_confirmed_upgrades')}",
        f"- New pending created: {summary.get('new_pending_created')}",
        f"- Paper order created: {summary.get('paper_order_created')}",
        "",
        "## Actions By Type",
        "| Action | Count |",
        "|---|---|",
    ]
    for action, count in (summary.get("actions_by_type") or {}).items():
        lines.append(f"| {action} | {count} |")
    lines.extend(["", "## Recent Actions", "| Created At | Evidence | Action | Before | After | Promotion Allowed |", "|---|---|---|---|---|---|"])
    for row in payload.get("recent_actions") or []:
        lines.append(
            f"| {row.get('created_at')} | {row.get('evidence_id')} | {row.get('action')} | {row.get('before_status')} | {row.get('after_status')} | {row.get('promotion_allowed_after_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 32 review action audit summary")
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
