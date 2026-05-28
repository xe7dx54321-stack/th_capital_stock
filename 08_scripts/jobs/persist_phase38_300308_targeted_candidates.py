#!/usr/bin/env python3
"""Persist a guarded Phase 38 sample of 300308.SZ targeted candidates."""

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
from smr_registry import register_snapshot
from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table, write_semantic_evidence_candidates
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_targeted_candidate_quality_review import build_targeted_candidate_quality_review, eligible_calibrated_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DEFAULT_LIMIT = 5


def _existing_ids(conn: sqlite3.Connection, candidate_ids: list[str]) -> set[str]:
    ensure_semantic_evidence_candidate_table(conn)
    if not candidate_ids:
        return set()
    placeholders = ",".join("?" for _ in candidate_ids)
    rows = conn.execute(
        f"SELECT evidence_id FROM semantic_evidence_candidates WHERE evidence_id IN ({placeholders})",
        candidate_ids,
    ).fetchall()
    return {str(row[0]) for row in rows}


def build_payload(
    conn: sqlite3.Connection,
    *,
    mode: str = "dry_run",
    limit: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    review = build_targeted_candidate_quality_review(conn, TARGET_TICKER)
    body = review.get("candidate_quality_review") or {}
    limit_value = DEFAULT_LIMIT if limit is None else max(1, int(limit))
    eligible = eligible_calibrated_candidates(review)
    if candidate_id:
        eligible = [candidate for candidate in eligible if candidate.get("evidence_id") == candidate_id]
    selected = eligible[:limit_value]
    ids = [str(candidate.get("evidence_id")) for candidate in selected if candidate.get("evidence_id")]
    existing = _existing_ids(conn, ids)
    to_write = [candidate for candidate in selected if str(candidate.get("evidence_id")) not in existing]
    written = 0
    if mode == "execute" and to_write:
        written = write_semantic_evidence_candidates(
            conn,
            to_write,
            enforce_quality_guard=True,
            min_quality_score=50,
            allow_review_required=False,
            reject_noisy=True,
        )
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "mode": mode,
        "persistence_result": {
            "candidates_total": body.get("candidates_reviewed", 0),
            "eligible_for_persistence": body.get("eligible_for_persistence", 0),
            "attempted_to_write": len(to_write) if mode == "execute" else len(selected),
            "selected_for_persistence": len(selected),
            "candidates_written": written,
            "duplicates_skipped": len(existing),
            "rejected_by_guard": max(0, len(to_write) - written) if mode == "execute" else 0,
            "usable_for_promotion_true": 0,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "selected_candidate_ids": ids,
            "written_candidate_ids": [str(candidate.get("evidence_id")) for candidate in to_write[:written]],
        },
        "safety": {
            "phase30_guard_used": True,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "limit_enforced": limit_value,
            "sensitive_confirmed_added": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist Phase 38 300308 targeted evidence candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--candidate-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, mode=mode, limit=args.limit, candidate_id=args.candidate_id)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase38_300308_targeted_candidate_persistence", TARGET_TICKER, mode, Path(__file__).name, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
