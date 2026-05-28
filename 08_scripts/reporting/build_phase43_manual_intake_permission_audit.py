#!/usr/bin/env python3
"""Build Phase 43 manual intake permission and allowed-usage audit."""

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
from smr_manual_intake_permission_guard import build_permission_audit
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_permission_audit(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("permission_audit") or {}
    lines = [f"# Phase 43 Manual Intake Permission Audit: {payload.get('ticker')}", "", "## Summary"]
    for key in ("manual_candidates_checked", "permission_passed", "permission_blocked", "allowed_usage_downgraded", "promotion_allowed_true"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Rows"])
    for row in body.get("audit_rows") or []:
        lines.append(f"- {row.get('candidate_id')}: {row.get('requested_allowed_usage')} -> {row.get('final_allowed_usage')}")
        if row.get("downgrade_reason"):
            lines.append(f"  Downgrade reason: {row.get('downgrade_reason')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 permission audit")
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
