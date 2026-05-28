#!/usr/bin/env python3
"""Controlled execution for Phase 41 specific evidence requests."""

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
from smr_research_followup_audit import write_followup_audit_record
from smr_research_followup_queue import CORE_EVIDENCE_TYPES, followup_item_id_for
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, get_lifecycle_by_ticker, normalize_ticker, review_candidate_id_for
from smr_specific_evidence_request import evidence_request_id_for, get_specific_evidence_request, upsert_specific_evidence_request
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _planned_types(evidence_type: str | None) -> list[str]:
    return [evidence_type] if evidence_type else list(CORE_EVIDENCE_TYPES)


def build_payload(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    evidence_type: str | None = None,
    mode: str = "dry_run",
) -> dict[str, Any]:
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"Unsupported mode: {mode}")
    ticker = normalize_ticker(ticker)
    request_types = _planned_types(evidence_type)
    lifecycle = get_lifecycle_by_ticker(conn, ticker)
    review_candidate_id = (lifecycle or {}).get("review_candidate_id") or review_candidate_id_for(ticker)
    planned_rows = []
    written_rows = []
    audit_rows = []
    duplicates = 0
    for request_type in request_types:
        request_id = evidence_request_id_for(ticker, request_type)
        existing = get_specific_evidence_request(conn, request_id)
        if existing:
            duplicates += 1
        planned_rows.append(
            {
                "request_id": request_id,
                "ticker": ticker,
                "evidence_type": request_type,
                "already_exists": bool(existing),
                "followup_item_id": followup_item_id_for(ticker, request_type),
            }
        )
        if mode == "execute":
            request = upsert_specific_evidence_request(
                conn,
                ticker=ticker,
                evidence_type=request_type,
                review_candidate_id=str(review_candidate_id),
                source_action="phase41_controlled_execute",
            )
            written_rows.append(request)
            audit_rows.append(
                write_followup_audit_record(
                    conn,
                    ticker=ticker,
                    followup_item_id=followup_item_id_for(ticker, request_type),
                    action="create_specific_evidence_request",
                    evidence_type=request_type,
                    before_status="open" if existing else "none",
                    after_status="open",
                    metadata={
                        "source_request_id": request.get("request_id"),
                        "request_not_evidence": True,
                        "pending_created": False,
                        "paper_order_created": False,
                        "promotion_allowed": False,
                    },
                )
            )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "specific_evidence_request_execution": {
            "mode": mode,
            "requests_planned": len(planned_rows),
            "requests_written": len(written_rows),
            "duplicates_skipped": duplicates,
            "audit_records_written": len(audit_rows),
            "request_types": request_types,
            "planned_rows": planned_rows,
            "written_rows": written_rows,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "safety": {
            "request_is_evidence": False,
            "official_consensus_confirmed": False,
            "supplier_share_confirmed": False,
            "customer_allocation_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Phase 41 specific evidence requests")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--evidence-type")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, evidence_type=args.evidence_type, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase41_specific_evidence_request_execution", args.ticker.upper(), mode, Path(__file__).name, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
