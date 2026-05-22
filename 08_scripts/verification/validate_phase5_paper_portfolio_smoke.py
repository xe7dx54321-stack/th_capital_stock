#!/usr/bin/env python3
"""Dry-run smoke validation for the paper-portfolio handoff chain."""

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
from smr_decision import ensure_decision_tables
from smr_paper_portfolio import ensure_paper_portfolio_tables, update_ledger_paper_trace
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase5_paper_portfolio_smoke.py"
SMOKE_STATUSES = ("pending_human_review", "approved_paper")


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def fetch_recommendation_ids(conn: sqlite3.Connection, recommendation_id: str | None, limit: int) -> list[str]:
    if recommendation_id:
        row = conn.execute(
            """
            SELECT recommendation_id
            FROM decision_ledger
            WHERE recommendation_id=?
            ORDER BY datetime(updated_at) DESC, id DESC
            LIMIT 1
            """,
            (recommendation_id,),
        ).fetchone()
        return [row[0]] if row else []
    rows = conn.execute(
        f"""
        SELECT recommendation_id
        FROM decision_ledger
        WHERE status IN ({",".join("?" for _ in SMOKE_STATUSES)})
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT ?
        """,
        (*SMOKE_STATUSES, limit),
    ).fetchall()
    return [row[0] for row in rows if row and row[0]]


def fetch_ledger_row(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT recommendation_id, ticker, market, action, status, updated_at, metadata_json
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "recommendation_id": row[0],
        "ticker": row[1],
        "market": row[2],
        "action": row[3],
        "status": row[4],
        "updated_at": row[5],
        "metadata": loads_json(row[6], {}),
    }


def fetch_review_transition(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT previous_status, new_status, review_action, reviewer, review_comment, created_at, metadata_json
        FROM recommendation_reviews
        WHERE recommendation_id=? AND review_action='approve_paper'
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "previous_status": row[0],
        "new_status": row[1],
        "review_action": row[2],
        "reviewer": row[3],
        "review_comment": row[4],
        "created_at": row[5],
        "metadata": loads_json(row[6], {}),
    }


def fetch_paper_order(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT order_id, ticker, market, side, order_type, status, reference_price, created_at, executed_at, metadata_json
        FROM paper_portfolio_orders
        WHERE recommendation_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "order_id": row[0],
        "ticker": row[1],
        "market": row[2],
        "side": row[3],
        "order_type": row[4],
        "status": row[5],
        "reference_price": row[6],
        "created_at": row[7],
        "executed_at": row[8],
        "metadata": loads_json(row[9], {}),
    }


def fetch_paper_position(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT position_id, ticker, market, quantity, avg_cost, position_pct, status, opened_at, closed_at, metadata_json
        FROM paper_portfolio_positions
        WHERE source_recommendation_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "position_id": row[0],
        "ticker": row[1],
        "market": row[2],
        "quantity": row[3],
        "avg_cost": row[4],
        "position_pct": row[5],
        "status": row[6],
        "opened_at": row[7],
        "closed_at": row[8],
        "metadata": loads_json(row[9], {}),
    }


def inspect_chain(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any]:
    ledger = fetch_ledger_row(conn, recommendation_id)
    if not ledger:
        return {
            "recommendation_id": recommendation_id,
            "chain_status": "missing",
            "missing_stages": ["decision_ledger"],
        }
    review_transition = fetch_review_transition(conn, recommendation_id)
    paper_order = fetch_paper_order(conn, recommendation_id)
    paper_position = fetch_paper_position(conn, recommendation_id)
    ledger_trace = (ledger.get("metadata") or {}).get("paper_portfolio") or {}
    if paper_order and paper_position and (
        ledger_trace.get("order_id") != paper_order.get("order_id")
        or ledger_trace.get("position_id") != paper_position.get("position_id")
    ):
        update_ledger_paper_trace(
            conn,
            recommendation_id,
            order=paper_order,
            position=paper_position,
            lifecycle_status="paper_position_open" if paper_position.get("status") == "open" else paper_position.get("status"),
        )
        ledger = fetch_ledger_row(conn, recommendation_id) or ledger
        ledger_trace = (ledger.get("metadata") or {}).get("paper_portfolio") or {}
    missing_stages = []
    if ledger.get("status") not in {"pending_human_review", "approved_paper"}:
        missing_stages.append(f"unexpected_status:{ledger.get('status')}")
    if not review_transition:
        missing_stages.append("approve_paper_transition")
    elif review_transition.get("previous_status") != "pending_human_review":
        missing_stages.append("review_previous_status")
    if not paper_order:
        missing_stages.append("paper_order")
    elif paper_order.get("status") != "executed":
        missing_stages.append("paper_order_executed")
    if not paper_position:
        missing_stages.append("paper_position")
    elif paper_position.get("status") != "open":
        missing_stages.append("paper_position_open")
    if not ledger_trace.get("order_id"):
        missing_stages.append("decision_ledger_order_trace")
    if not ledger_trace.get("position_id"):
        missing_stages.append("decision_ledger_position_trace")
    complete = (
        review_transition is not None
        and review_transition.get("new_status") == "approved_paper"
        and review_transition.get("previous_status") == "pending_human_review"
        and paper_order is not None
        and paper_order.get("status") == "executed"
        and paper_position is not None
        and paper_position.get("status") == "open"
        and ledger_trace.get("order_id") == paper_order.get("order_id")
        and ledger_trace.get("position_id") == paper_position.get("position_id")
    )
    return {
        "recommendation_id": recommendation_id,
        "ticker": ledger.get("ticker"),
        "market": ledger.get("market"),
        "current_status": ledger.get("status"),
        "chain_status": "complete" if complete else "incomplete",
        "missing_stages": list(dict.fromkeys(missing_stages)),
        "review_transition": review_transition,
        "paper_order": paper_order,
        "paper_position": paper_position,
        "ledger_trace": ledger_trace,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {
            "overall_result": "skipped",
            "skip_reason": "no pending_human_review or approved_paper recommendations found",
            "candidate_count": 0,
            "complete_chain_count": 0,
            "incomplete_chain_count": 0,
        }
    complete = sum(1 for item in results if item.get("chain_status") == "complete")
    incomplete = len(results) - complete
    return {
        "overall_result": "pass" if complete else "partial_pass",
        "candidate_count": len(results),
        "complete_chain_count": complete,
        "incomplete_chain_count": incomplete,
        "skip_reason": None,
    }


def compact_result(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "recommendation_id": item.get("recommendation_id"),
        "ticker": item.get("ticker"),
        "market": item.get("market"),
        "current_status": item.get("current_status"),
        "chain_status": item.get("chain_status"),
        "missing_stages": item.get("missing_stages") or [],
        "review_transition": item.get("review_transition"),
        "paper_order": item.get("paper_order"),
        "paper_position": item.get("paper_position"),
        "ledger_trace": item.get("ledger_trace"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate paper portfolio smoke checkpoint")
    parser.add_argument("--recommendation-id", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_decision_tables(conn)
        ensure_paper_portfolio_tables(conn)
        recommendation_ids = fetch_recommendation_ids(conn, args.recommendation_id, args.limit)
        results = [inspect_chain(conn, recommendation_id) for recommendation_id in recommendation_ids]
        payload = {
            "generated_at": now_ts(),
            "mode": "paper_portfolio_smoke_dry_run",
            "dry_run": True,
            "summary": summarize(results),
            "results": [compact_result(item) for item in results],
            "full_payload_location": "task_registry_entry entity_type=phase5_paper_portfolio_smoke_validation entity_id=latest",
        }
        register_snapshot(
            conn,
            entity_type="phase5_paper_portfolio_smoke_validation",
            entity_id="latest",
            status=payload["summary"]["overall_result"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "paper portfolio smoke validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
