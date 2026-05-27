#!/usr/bin/env python3
"""Build Phase 33 governance delta dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase31_evidence_governance_dashboard import build_payload as build_governance_dashboard
from smr_agents import DB_PATH
from smr_controlled_review_plan import phase33_audits
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    governance = build_governance_dashboard(conn)
    audits = phase33_audits(conn)
    after_counts = Counter(row.get("after_status") for row in audits)
    action_counts = Counter(row.get("action") for row in audits)
    summary = dict(governance.get("summary") or {})
    pending_delta = -sum(1 for row in audits if row.get("before_status") == "pending_review" and row.get("after_status") != "pending_review")
    summary.update(
        {
            "approved_evidence": after_counts.get("approved_evidence", summary.get("approved_evidence", 0)),
            "rejected_evidence": after_counts.get("rejected_evidence", summary.get("rejected_evidence", 0)),
            "downgraded_evidence": after_counts.get("downgraded_evidence", 0),
            "marked_noise": after_counts.get("marked_noise", summary.get("marked_noise", 0)),
            "needs_better_source": after_counts.get("needs_better_source", summary.get("needs_better_source", 0)),
            "pending_review_delta": pending_delta,
            "promotion_allowed_true": summary.get("promotion_allowed_true", 0),
            "new_pending_created": 0,
        }
    )
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "phase33_action_counts": dict(action_counts),
        "audit_records": len(audits),
        "safety": {
            "read_only_delta": True,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 33 Governance Delta Dashboard",
        "",
        "## Overall",
        f"- Total semantic evidence: {summary.get('total_semantic_evidence')}",
        f"- Approved evidence: {summary.get('approved_evidence')}",
        f"- Rejected evidence: {summary.get('rejected_evidence')}",
        f"- Downgraded evidence: {summary.get('downgraded_evidence')}",
        f"- Marked noise: {summary.get('marked_noise')}",
        f"- Needs better source: {summary.get('needs_better_source')}",
        f"- Pending review delta: {summary.get('pending_review_delta')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        f"- New pending created: {summary.get('new_pending_created')}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 33 governance delta dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
