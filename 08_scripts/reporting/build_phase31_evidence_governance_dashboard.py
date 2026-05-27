#!/usr/bin/env python3
"""Build Phase 31 evidence governance dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_download_repair_queue import list_download_repair_tasks
from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates
from smr_evidence_review_queue import build_review_queue_with_generated_candidates
from smr_sensitive_variable_guard import is_sensitive_variable
from smr_supply_chain_variable_evidence import SEMANTIC_VARIABLE_MAP
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _synthetic_status(candidate: dict) -> str:
    payload = candidate.get("payload") or {}
    bucket = ((payload.get("quality") or {}).get("quality_bucket")) or "usable"
    return "pending_review" if bucket in {"review_required", "weak_but_usable"} else "persisted_candidate"


def build_payload(conn: sqlite3.Connection) -> dict:
    candidates = list_semantic_evidence_candidates(conn)
    states_by_id = {state.get("evidence_id"): state for state in list_lifecycle_states(conn)}
    queue = build_review_queue_with_generated_candidates(conn)
    repair_tasks = list_download_repair_tasks(conn)
    status_counts: Counter[str] = Counter()
    by_ticker: dict[str, dict] = defaultdict(lambda: {"semantic_evidence": 0, "pending_review": 0, "linked_to_variable_pack": 0, "top_variables": Counter(), "sensitive_variable_flags": set()})
    for candidate in candidates:
        state = states_by_id.get(candidate.get("evidence_id")) or {}
        status = state.get("lifecycle_status") or _synthetic_status(candidate)
        status_counts[status] += 1
        ticker = candidate.get("ticker")
        row = by_ticker[ticker]
        row["semantic_evidence"] += 1
        if status == "pending_review":
            row["pending_review"] += 1
        pack = SEMANTIC_VARIABLE_MAP.get(str(candidate.get("variable_type")))
        if pack:
            row["linked_to_variable_pack"] += 1
            row["top_variables"][pack] += 1
        if is_sensitive_variable(candidate.get("variable_type")):
            row["sensitive_variable_flags"].add(str(candidate.get("variable_type")))
    by_ticker_rows = []
    for ticker, row in sorted(by_ticker.items()):
        top_variables = [item for item, _ in row["top_variables"].most_common(4)]
        by_ticker_rows.append(
            {
                "ticker": ticker,
                "semantic_evidence": row["semantic_evidence"],
                "pending_review": row["pending_review"],
                "linked_to_variable_pack": row["linked_to_variable_pack"],
                "top_variables": top_variables,
                "sensitive_variable_flags": sorted(row["sensitive_variable_flags"]),
            }
        )
    sensitive_count = sum(1 for candidate in candidates if is_sensitive_variable(candidate.get("variable_type")))
    queue_summary = queue.get("summary") or {}
    queue_pending_review = sum(
        1
        for item in queue.get("items") or []
        if "review_required" in (item.get("review_reason") or [])
        or "review_required_quality_bucket" in (item.get("review_reason") or [])
        or item.get("lifecycle_status") == "pending_review"
    )
    return {
        "generated_at": now_ts(),
        "summary": {
            "total_semantic_evidence": len(candidates),
            "pending_review": status_counts.get("pending_review", 0) + queue_pending_review,
            "approved_evidence": status_counts.get("approved_evidence", 0),
            "rejected_evidence": status_counts.get("rejected_evidence", 0),
            "marked_noise": status_counts.get("marked_noise", 0),
            "needs_better_source": status_counts.get("needs_better_source", 0) + sum(1 for task in repair_tasks if task.get("status") == "open"),
            "linked_to_variable_pack": sum(row.get("linked_to_variable_pack", 0) for row in by_ticker_rows),
            "sensitive_variable_items": sensitive_count + queue_summary.get("sensitive_variable_items", 0),
            "promotion_allowed_true": sum(1 for candidate in candidates if candidate.get("usable_for_promotion")),
            "new_pending_created": 0,
        },
        "by_ticker": by_ticker_rows,
        "risk_flags": [
            {"flag": "sensitive_variable_requires_review", "count": sensitive_count},
            {"flag": "download_repair_open", "count": sum(1 for task in repair_tasks if task.get("status") == "open")},
        ],
        "safety": {
            "promotion_rules_relaxed": False,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 31 Evidence Governance Dashboard",
        "",
        "## Overall",
        f"- Total semantic evidence: {summary.get('total_semantic_evidence')}",
        f"- Pending review: {summary.get('pending_review')}",
        f"- Approved evidence: {summary.get('approved_evidence')}",
        f"- Rejected evidence: {summary.get('rejected_evidence')}",
        f"- Needs better source: {summary.get('needs_better_source')}",
        f"- Linked to variable pack: {summary.get('linked_to_variable_pack')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Ticker",
        "| Ticker | Evidence | Pending Review | Linked Variables | Sensitive Flags |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("by_ticker") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('semantic_evidence')} | {row.get('pending_review')} | {row.get('linked_to_variable_pack')} | {', '.join(row.get('sensitive_variable_flags') or [])} |"
        )
    lines.extend(["", "## Risk Flags", "| Flag | Count |", "|---|---|"])
    for row in payload.get("risk_flags") or []:
        lines.append(f"| {row.get('flag')} | {row.get('count')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 31 evidence governance dashboard")
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
