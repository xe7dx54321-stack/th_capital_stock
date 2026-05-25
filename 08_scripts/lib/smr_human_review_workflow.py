#!/usr/bin/env python3
"""Human review workflow helpers for Phase 15."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_decision import (
    build_review_audit_metadata,
    ensure_decision_tables,
    latest_decision_ledger_row,
    loads,
    review_audit_detail_from_metadata,
    review_recommendation,
)
from smr_paper_portfolio import ensure_paper_portfolio_tables


NEXT_ALLOWED_ACTIONS = [
    "approve_paper",
    "reject",
    "downgrade",
    "request_more_research",
    "reduce_position_size",
    "archive",
]


def resolve_recommendation_id(conn: sqlite3.Connection, recommendation_id: str) -> str:
    """Resolve friendly Phase aliases to the persisted recommendation id."""

    ensure_decision_tables(conn)
    if latest_decision_ledger_row(conn, recommendation_id):
        return recommendation_id
    text = str(recommendation_id or "")
    aliases = []
    if text.startswith("phase14__"):
        aliases.append(text.replace("phase14__", "phase14_thesis_aware__", 1))
    if text.startswith("phase13__"):
        aliases.append(text.replace("phase13__", "phase13_core_gate__", 1))
    for alias in aliases:
        if latest_decision_ledger_row(conn, alias):
            return alias
    ticker = None
    parts = text.split("__")
    if len(parts) >= 2:
        ticker = parts[1]
    if ticker:
        row = conn.execute(
            """
            SELECT recommendation_id
            FROM decision_ledger
            WHERE ticker=? AND status='pending_human_review'
            ORDER BY datetime(updated_at) DESC, id DESC
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()
        if row:
            return str(row[0])
    return recommendation_id


def _latest_order_status(conn: sqlite3.Connection, recommendation_id: str) -> str | None:
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='paper_portfolio_orders'"
    ).fetchone():
        return None
    row = conn.execute(
        """
        SELECT status
        FROM paper_portfolio_orders
        WHERE recommendation_id=?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    return row[0] if row else None


def _portfolio_projection(conn: sqlite3.Connection, row: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    ensure_paper_portfolio_tables(conn)
    position_pct = row.get("suggested_position_pct")
    if position_pct is None:
        position_pct = (metadata.get("candidate") or {}).get("suggested_position_pct")
    current_total = 0.0
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='paper_portfolio_positions'"
    ).fetchone():
        current_total = float(
            conn.execute(
                "SELECT SUM(COALESCE(position_pct, 0)) FROM paper_portfolio_positions WHERE status='open'"
            ).fetchone()[0]
            or 0.0
        )
    return {
        "status": metadata.get("portfolio_risk_status") or (metadata.get("portfolio_risk") or {}).get("status"),
        "projected_position_pct": float(position_pct or 0.0),
        "current_exposure_total": round(current_total, 4),
        "projected_exposure_total_if_approved": round(current_total + float(position_pct or 0.0), 4),
    }


def review_queue_item_from_row(conn: sqlite3.Connection, row: dict[str, Any]) -> dict[str, Any]:
    metadata = build_review_audit_metadata(row.get("metadata") or {}, status=row.get("status"))
    detail = review_audit_detail_from_metadata(
        str(row.get("recommendation_id")),
        metadata,
        status=str(row.get("status")),
        ticker=row.get("ticker"),
    )
    candidate = metadata.get("candidate") or {}
    thesis_inference = metadata.get("thesis_inference") or {}
    return {
        "recommendation_id": row.get("recommendation_id"),
        "ticker": row.get("ticker") or metadata.get("ticker") or candidate.get("ticker"),
        "market": row.get("market") or metadata.get("market"),
        "status": row.get("status"),
        "action": row.get("action"),
        "promotion_mode": metadata.get("promotion_mode"),
        "position_policy": metadata.get("position_policy"),
        "suggested_position_pct": row.get("suggested_position_pct") if row.get("suggested_position_pct") is not None else candidate.get("suggested_position_pct"),
        "primary_thesis_type": metadata.get("primary_thesis_type"),
        "thesis_inference_confidence": metadata.get("thesis_inference_confidence") or thesis_inference.get("confidence"),
        "requires_human_review": bool(metadata.get("requires_human_review")),
        "auto_approval_allowed": bool(metadata.get("auto_approval_allowed")),
        "paper_order_allowed": bool(metadata.get("paper_order_allowed")),
        "core_blockers": metadata.get("core_blockers") or [],
        "supporting_warnings": metadata.get("supporting_warnings") or [],
        "optional_warnings": metadata.get("optional_warnings") or [],
        "data_quality_gate": metadata.get("data_quality_gate") or metadata.get("data_quality_gate_status"),
        "bear_case_gate": detail.get("bear_case_gate") or {},
        "portfolio_risk": _portfolio_projection(conn, row, metadata),
        "paper_order_status": _latest_order_status(conn, str(row.get("recommendation_id"))),
        "next_allowed_actions": list(NEXT_ALLOWED_ACTIONS),
        "audit_flags": metadata.get("audit_flags") or [],
        "updated_at": row.get("updated_at"),
    }


def list_review_queue(conn: sqlite3.Connection, *, include_non_pending: bool = False) -> list[dict[str, Any]]:
    ensure_decision_tables(conn)
    where = "status='pending_human_review'" if not include_non_pending else "status IN ('pending_human_review', 'needs_more_research')"
    rows = conn.execute(
        f"""
        SELECT recommendation_id, ticker, market, action, status, suggested_position_pct,
               max_position_pct, metadata_json, updated_at
        FROM decision_ledger
        WHERE {where}
        ORDER BY datetime(updated_at) DESC, id DESC
        """
    ).fetchall()
    items = []
    seen: set[str] = set()
    for row in rows:
        rec_id = str(row[0])
        if rec_id in seen:
            continue
        seen.add(rec_id)
        items.append(
            review_queue_item_from_row(
                conn,
                {
                    "recommendation_id": rec_id,
                    "ticker": row[1],
                    "market": row[2],
                    "action": row[3],
                    "status": row[4],
                    "suggested_position_pct": row[5],
                    "max_position_pct": row[6],
                    "metadata": loads(row[7], {}),
                    "updated_at": row[8],
                },
            )
        )
    return items


def get_review_detail(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any]:
    resolved_id = resolve_recommendation_id(conn, recommendation_id)
    row = latest_decision_ledger_row(conn, resolved_id)
    if not row:
        return {"recommendation_id": recommendation_id, "found": False}
    item = review_queue_item_from_row(conn, row)
    metadata = build_review_audit_metadata(row.get("metadata") or {}, status=row.get("status"))
    return {
        **item,
        "found": True,
        "requested_recommendation_id": recommendation_id,
        "resolved_recommendation_id": resolved_id,
        "thesis": {
            "primary_thesis_type": metadata.get("primary_thesis_type"),
            "thesis_inference_confidence": metadata.get("thesis_inference_confidence"),
            "thesis_inference": metadata.get("thesis_inference") or {},
            "dependency_map": (metadata.get("promotion_evidence_gate") or {}).get("field_dependency") or {},
        },
        "field_gate": {
            "core_blockers": metadata.get("core_blockers") or [],
            "supporting_warnings": metadata.get("supporting_warnings") or [],
            "optional_warnings": metadata.get("optional_warnings") or [],
        },
        "data_quality_gate_detail": metadata.get("data_quality_gate_detail") or metadata.get("data_quality_gate") or {},
        "valuation": metadata.get("valuation") or (metadata.get("promotion_result") or {}).get("snapshots", {}).get("valuation_snapshot") or {},
        "portfolio_impact": _portfolio_projection(conn, row, metadata),
        "hard_audit_flags": {
            "requires_human_review": bool(metadata.get("requires_human_review")),
            "auto_approval_allowed": bool(metadata.get("auto_approval_allowed")),
            "paper_order_allowed": bool(metadata.get("paper_order_allowed")),
        },
    }


def apply_human_review_action(
    conn: sqlite3.Connection,
    *,
    recommendation_id: str,
    action: str,
    reviewer: str | None,
    note: str,
    new_position_pct: float | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    resolved_id = resolve_recommendation_id(conn, recommendation_id)
    before = get_review_detail(conn, resolved_id)
    if not before.get("found"):
        raise ValueError(f"recommendation not found: {recommendation_id}")
    overrides: dict[str, Any] = {}
    if new_position_pct is not None:
        overrides["new_position_pct"] = new_position_pct
    if dry_run:
        if action == "approve_paper" and before.get("status") != "pending_human_review":
            allowed = False
            reason = "approve_paper requires pending_human_review status"
        elif action == "reduce_position_size" and new_position_pct is None:
            allowed = False
            reason = "reduce_position_size requires --new-position-pct"
        elif action == "reduce_position_size" and float(new_position_pct) > float(before.get("suggested_position_pct") or 0.0):
            allowed = False
            reason = "reduce_position_size cannot increase suggested_position_pct"
        else:
            allowed = True
            reason = "dry_run_only"
        return {
            "mode": "dry_run",
            "recommendation_id": resolved_id,
            "requested_recommendation_id": recommendation_id,
            "action": action,
            "allowed": allowed,
            "reason": reason,
            "previous_status": before.get("status"),
            "would_new_status": {
                "approve_paper": "approved_paper",
                "reject": "rejected",
                "downgrade": "candidate_shadow",
                "request_more_research": "needs_more_research",
                "reduce_position_size": "pending_human_review",
                "archive": "archived",
            }.get(action),
            "previous_position_pct": before.get("suggested_position_pct"),
            "would_new_position_pct": new_position_pct if new_position_pct is not None else before.get("suggested_position_pct"),
            "would_write_human_review_actions": allowed,
            "would_write_decision_ledger": allowed,
        }
    result = review_recommendation(
        conn,
        resolved_id,
        reviewer=reviewer,
        action=action,
        comment=note,
        overrides=overrides,
    )
    after = get_review_detail(conn, resolved_id)
    return {
        "mode": "execute",
        "recommendation_id": resolved_id,
        "requested_recommendation_id": recommendation_id,
        "action": action,
        "allowed": True,
        "review_result": result,
        "after_status": after.get("status"),
        "after_position_pct": after.get("suggested_position_pct"),
        "human_review_action_written": True,
        "decision_ledger_written": True,
    }
