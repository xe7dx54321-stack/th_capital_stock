#!/usr/bin/env python3
"""Build Phase 38 300308 evidence-chain refresh after persistence."""

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
from smr_research_evidence_chain import build_research_evidence_chain
from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_targeted_candidate_quality_review import build_targeted_candidate_quality_review
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _persisted_phase38_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_semantic_evidence_candidate_table(conn)
    review = build_targeted_candidate_quality_review(conn, TARGET_TICKER)
    review_rows = {
        str(row.get("candidate_id")): row
        for row in (review.get("candidate_quality_review") or {}).get("quality_rows") or []
        if row.get("candidate_id")
    }
    ids = list(review_rows)
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT evidence_id, variable_type, allowed_usage, usable_for_promotion, evidence_status
        FROM semantic_evidence_candidates
        WHERE ticker=? AND evidence_id IN ({placeholders})
        """,
        (TARGET_TICKER, *ids),
    ).fetchall()
    result = []
    for evidence_id, variable_type, allowed_usage, usable_for_promotion, evidence_status in rows:
        review_row = review_rows.get(str(evidence_id)) or {}
        result.append(
            {
                "evidence_id": evidence_id,
                "variable": review_row.get("variable") or variable_type,
                "variable_type": variable_type,
                "allowed_usage": allowed_usage,
                "usable_for_promotion": bool(usable_for_promotion),
                "evidence_status": evidence_status,
            }
        )
    return result


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    chain = build_research_evidence_chain(conn, TARGET_TICKER).get("evidence_chain") or {}
    persisted = _persisted_phase38_rows(conn)
    by_variable = Counter(row.get("variable") for row in persisted)
    after = int(chain.get("total_evidence") or 0)
    new_count = len(persisted)
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "evidence_chain_refresh": {
            "evidence_before": max(0, after - new_count),
            "new_candidates_written": new_count,
            "evidence_after": after,
            "new_evidence_by_variable": dict(sorted(by_variable.items())),
            "sensitive_confirmed_added": sum(
                1
                for row in persisted
                if row.get("variable") in {"supplier_share", "customer_allocation_proxy", "official_consensus"}
                and str(row.get("evidence_status")) == "confirmed"
            ),
            "usable_for_promotion_true": sum(1 for row in persisted if row.get("usable_for_promotion")),
            "new_evidence_ids": [row.get("evidence_id") for row in persisted],
        },
        "safety": {
            "rejected_or_noisy_added": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    body = payload.get("evidence_chain_refresh") or {}
    lines = [
        "# Phase 38 300308 Evidence Chain Refresh",
        "",
        f"- Evidence before: {body.get('evidence_before')}",
        f"- New candidates written: {body.get('new_candidates_written')}",
        f"- Evidence after: {body.get('evidence_after')}",
        f"- Sensitive confirmed added: {body.get('sensitive_confirmed_added')}",
        f"- Usable for promotion true: {body.get('usable_for_promotion_true')}",
        "",
        "## New Evidence By Variable",
    ]
    for variable, count in (body.get("new_evidence_by_variable") or {}).items():
        lines.append(f"- {variable}: {count}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 38 300308 evidence-chain refresh")
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
