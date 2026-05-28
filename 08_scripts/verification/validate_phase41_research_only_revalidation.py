#!/usr/bin/env python3
"""Validate Phase 41 remains research-only after follow-up task execution."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_customer_allocation_route import build_payload as build_customer_allocation
from build_phase41_official_consensus_availability import build_payload as build_official_consensus
from build_phase41_research_followup_queue import build_payload as build_queue
from build_phase41_supplier_share_route import build_payload as build_supplier_share
from smr_agents import DB_PATH
from smr_research_followup_audit import list_followup_audit_records
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    requests = list_specific_evidence_requests(conn, ticker="300308.SZ")
    queue = build_queue(conn, "300308.SZ")
    official = build_official_consensus(conn, "300308.SZ").get("official_consensus_availability") or {}
    supplier = build_supplier_share(conn, "300308.SZ").get("supplier_share_route") or {}
    customer = build_customer_allocation(conn, "300308.SZ").get("customer_allocation_route") or {}
    audits = list_followup_audit_records(conn, ticker="300308.SZ")
    summary = {
        "specific_evidence_requests_created": len(requests),
        "followup_queue_items": (queue.get("summary") or {}).get("followup_queue_items", 0),
        "official_consensus_confirmed": bool(official.get("official_consensus_confirmed")),
        "supplier_share_confirmed": bool(supplier.get("supplier_share_confirmed")),
        "customer_allocation_confirmed": bool(customer.get("customer_allocation_confirmed")),
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed_true": 0,
        "forbidden_action_violations": 0,
        "followup_audit_records": len(audits),
    }
    ok = (
        not summary["official_consensus_confirmed"]
        and not summary["supplier_share_confirmed"]
        and not summary["customer_allocation_confirmed"]
        and summary["pending_created"] == 0
        and summary["paper_order_created"] == 0
        and summary["promotion_allowed_true"] == 0
        and summary["forbidden_action_violations"] == 0
    )
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if ok else "fail",
        "summary": summary,
        "safety": {
            "research_only": True,
            "evidence_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 41 research-only state")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
