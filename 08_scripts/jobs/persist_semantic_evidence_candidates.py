#!/usr/bin/env python3
"""Persist Phase 28 semantic evidence candidates."""

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
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_semantic_evidence_persistence import (
    build_semantic_evidence_candidates,
    delete_semantic_evidence_candidates,
    flatten_candidates,
    guard_semantic_evidence_candidates,
    write_semantic_evidence_candidates,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "persist_semantic_evidence_candidates.py"


def build_payload(
    conn: sqlite3.Connection,
    *,
    tickers: str | None = None,
    mode: str = "dry_run",
    use_text_cache: bool = False,
    min_quality_score: int = 50,
    allow_review_required: bool = False,
    quality_report: bool = False,
    reject_noisy: bool = True,
) -> dict:
    candidate_payload = build_semantic_evidence_candidates(
        conn,
        tickers,
        use_real_sources=True,
        allow_mock_fallback=True,
        mode="mock",
        use_text_cache=use_text_cache,
        extract_text_if_missing=False,
        skip_metadata_only=True,
    )
    candidates = flatten_candidates(candidate_payload)
    guarded = guard_semantic_evidence_candidates(
        candidates,
        min_quality_score=min_quality_score,
        allow_review_required=allow_review_required,
        reject_noisy=reject_noisy,
    )
    eligible = guarded["eligible_candidates"]
    written = 0
    removed = 0
    if mode == "execute":
        written = write_semantic_evidence_candidates(
            conn,
            eligible,
            enforce_quality_guard=True,
            min_quality_score=min_quality_score,
            allow_review_required=allow_review_required,
            reject_noisy=reject_noisy,
        )
        removed = delete_semantic_evidence_candidates(
            conn,
            guarded["rejected_candidates"] + guarded["review_required_candidates"],
        )
    guarded_by_id = {item.get("evidence_id"): item for item in guarded["scored_candidates"]}
    return {
        "generated_at": candidate_payload.get("generated_at"),
        "mode": mode,
        "summary": {
            **(candidate_payload.get("summary") or {}),
            "evidence_candidates_created": len(candidates),
            "candidates_created": len(candidates),
            **(guarded.get("summary") or {}),
            "evidence_candidates_written": written,
            "evidence_candidates_removed": removed,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "new_pending_created": 0,
        },
        "rows": [
            {
                "ticker": row.get("ticker"),
                "evidence_candidates": [
                    {
                        **candidate,
                        **({"quality": guarded_by_id.get(candidate.get("evidence_id"), {}).get("quality")} if quality_report else {}),
                    }
                    for candidate in row.get("evidence_candidates") or []
                ],
                "candidate_count": len(row.get("evidence_candidates") or []),
                "eligible_for_persistence": sum(1 for candidate in row.get("evidence_candidates") or [] if candidate.get("evidence_id") in {item.get("evidence_id") for item in eligible}),
            }
            for row in candidate_payload.get("rows") or []
        ],
        "quality_report": {
            "enabled": bool(quality_report),
            "quality_assessments": guarded["quality_assessments"] if quality_report else [],
        },
        "safety": {
            "raw_source_text_written": False,
            "semantic_evidence_direct_promotion": False,
            "paper_order_created": False,
            "real_trade_risk": False,
            "usable_for_promotion_true": (guarded.get("summary") or {}).get("usable_for_promotion_true", 0),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist semantic evidence candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--use-text-cache", action="store_true")
    parser.add_argument("--min-quality-score", type=int, default=50)
    parser.add_argument("--allow-review-required", action="store_true")
    parser.add_argument("--quality-report", action="store_true")
    parser.add_argument("--reject-noisy", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(
            conn,
            tickers=args.tickers,
            mode=mode,
            use_text_cache=args.use_text_cache,
            min_quality_score=args.min_quality_score,
            allow_review_required=args.allow_review_required,
            quality_report=args.quality_report,
            reject_noisy=args.reject_noisy or mode == "execute",
        )
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase28_semantic_evidence_candidates", args.tickers or "supply_chain_pilot", mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase28 semantic evidence candidates persisted", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
