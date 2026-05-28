#!/usr/bin/env python3
"""Build Phase 38 targeted review queue for 300308.SZ candidates."""

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
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_targeted_candidate_quality_review import build_targeted_candidate_quality_review
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _queue_reason(row: dict[str, Any]) -> list[str]:
    reasons = list(row.get("review_reasons") or [])
    if row.get("quality_bucket") in {"review_required", "weak_but_usable"}:
        reasons.append(str(row.get("quality_bucket")))
    if row.get("recommended_action") == "reject":
        reasons.append("rejected_for_audit")
    if row.get("duplication_risk"):
        reasons.append("duplicate_risk")
    return list(dict.fromkeys(reason for reason in reasons if reason))


def _recommended_queue_action(row: dict[str, Any]) -> str:
    if row.get("recommended_action") == "reject":
        return "audit_reject"
    if row.get("variable") == "customer_allocation_proxy":
        return "downgrade_usage"
    if row.get("recommended_action") == "review_required":
        return "manual_review_before_persistence"
    return "review_caveat_before_execute"


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    review = build_targeted_candidate_quality_review(conn, TARGET_TICKER)
    rows = (review.get("candidate_quality_review") or {}).get("quality_rows") or []
    items = []
    for row in rows:
        reasons = _queue_reason(row)
        if not reasons:
            continue
        if row.get("recommended_action") == "persist_candidate" and not (
            row.get("variable") == "customer_allocation_proxy"
            or row.get("quality_bucket") == "weak_but_usable"
            or row.get("duplication_risk")
            or "no_explicit_asp_or_price" in reasons
        ):
            continue
        candidate_id = row.get("candidate_id")
        items.append(
            {
                "candidate_id": candidate_id,
                "variable": row.get("variable"),
                "quality_bucket": row.get("quality_bucket"),
                "recommended_action": _recommended_queue_action(row),
                "review_reason": reasons,
                "dry_run_command": (
                    "python 08_scripts/jobs/persist_phase38_300308_targeted_candidates.py "
                    f"--dry-run --candidate-id {candidate_id} --json"
                ),
                "execute_command_generated": False,
            }
        )
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "targeted_review_queue": {
            "queue_items": len(items),
            "high_priority_review": sum(1 for item in items if item.get("variable") in {"customer_allocation_proxy", "ASP_price_proxy"}),
            "sensitive_variable_items": sum(1 for item in items if item.get("variable") == "customer_allocation_proxy"),
            "review_required": sum(1 for item in items if "review_required" in item.get("review_reason", [])),
            "rejected_for_audit": sum(1 for item in items if "rejected_for_audit" in item.get("review_reason", [])),
            "items": items,
        },
        "safety": {
            "queue_written_to_db": False,
            "execute_command_generated": False,
            "sensitive_item_recommends_approve": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    queue = payload.get("targeted_review_queue") or {}
    lines = [
        "# Phase 38 300308 Targeted Review Queue",
        "",
        f"- Queue items: {queue.get('queue_items')}",
        f"- Sensitive variable items: {queue.get('sensitive_variable_items')}",
        "",
        "| Candidate | Variable | Action | Reasons | Dry Run |",
        "|---|---|---|---|---|",
    ]
    for item in queue.get("items") or []:
        lines.append(
            f"| {item.get('candidate_id')} | {item.get('variable')} | {item.get('recommended_action')} | "
            f"{', '.join(item.get('review_reason') or [])} | `{item.get('dry_run_command')}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 targeted review queue")
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
