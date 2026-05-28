#!/usr/bin/env python3
"""Phase 40 research-review lifecycle state.

This layer is research-only. It intentionally cannot create investment pending
items, approved papers, paper orders, positions, or promotion state.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_research_review_candidate import build_research_review_candidate_decision
from smr_wiki import now_ts


TARGET_REVIEW_TICKER = "300308.SZ"
REPAIR_ONLY_TICKER = "300394.SZ"
DEFAULT_COMPANY_NAMES = {
    "300308.SZ": "中际旭创",
    "300394.SZ": "天孚通信",
}

RESEARCH_REVIEW_STATUSES = {
    "research_review_candidate",
    "in_research_review",
    "reviewed_continue_evidence",
    "reviewed_request_deeper_research",
    "reviewed_request_specific_evidence",
    "reviewed_deprioritize",
    "reviewed_archive",
    "reviewed_no_action",
    "repair_required_before_review",
    "unknown",
}

REVIEW_ACTION_STATUSES = {
    "not_started",
    "in_progress",
    "reviewed",
    "needs_follow_up",
    "archived",
    "blocked",
}

FORBIDDEN_INVESTMENT_STATUSES = {
    "pending_human_review",
    "approved_paper",
    "paper_order",
    "paper_position",
    "investment_candidate",
    "promoted",
}


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or TARGET_REVIEW_TICKER).strip().upper()


def review_candidate_id_for(ticker: str, source_phase: str = "phase39") -> str:
    normalized = normalize_ticker(ticker).lower().replace(".", "_")
    return f"research_review_{normalized}_{source_phase}"


def ensure_research_review_lifecycle_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS research_review_lifecycle (
            review_candidate_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT,
            research_review_status TEXT NOT NULL,
            review_action_status TEXT NOT NULL,
            source_phase TEXT NOT NULL,
            decision_confidence TEXT,
            pending_allowed INTEGER NOT NULL DEFAULT 0,
            paper_order_allowed INTEGER NOT NULL DEFAULT 0,
            promotion_allowed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_reviewed_at TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_research_review_lifecycle_ticker
        ON research_review_lifecycle(ticker, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_research_review_lifecycle_status
        ON research_review_lifecycle(research_review_status, review_action_status, updated_at DESC);
        """
    )


def _row_to_dict(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any]:
    if not row:
        return {}
    keys = [
        "review_candidate_id",
        "ticker",
        "company_name",
        "research_review_status",
        "review_action_status",
        "source_phase",
        "decision_confidence",
        "pending_allowed",
        "paper_order_allowed",
        "promotion_allowed",
        "created_at",
        "updated_at",
        "last_reviewed_at",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["pending_allowed"] = bool(data.get("pending_allowed"))
    data["paper_order_allowed"] = bool(data.get("paper_order_allowed"))
    data["promotion_allowed"] = bool(data.get("promotion_allowed"))
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def validate_lifecycle_object(lifecycle: dict[str, Any]) -> None:
    status = str(lifecycle.get("research_review_status") or "")
    action_status = str(lifecycle.get("review_action_status") or "")
    if status not in RESEARCH_REVIEW_STATUSES:
        raise ValueError(f"Unsupported research review status: {status}")
    if action_status not in REVIEW_ACTION_STATUSES:
        raise ValueError(f"Unsupported review action status: {action_status}")
    if status in FORBIDDEN_INVESTMENT_STATUSES:
        raise ValueError(f"Forbidden investment status in research lifecycle: {status}")
    if lifecycle.get("pending_allowed") or lifecycle.get("paper_order_allowed") or lifecycle.get("promotion_allowed"):
        raise ValueError("Research-review lifecycle must keep pending/order/promotion disabled")


def validate_status_transition(before_status: str, after_status: str) -> None:
    before_status = str(before_status or "unknown")
    after_status = str(after_status or "unknown")
    if after_status not in RESEARCH_REVIEW_STATUSES:
        raise ValueError(f"Unsupported research review status: {after_status}")
    if after_status in FORBIDDEN_INVESTMENT_STATUSES or "pending" in after_status and after_status != "repair_required_before_review":
        raise ValueError(f"Research review cannot transition to investment state: {after_status}")
    if before_status not in RESEARCH_REVIEW_STATUSES:
        raise ValueError(f"Unsupported prior research review status: {before_status}")


def build_phase39_lifecycle_object(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    created = now_ts()
    if ticker == REPAIR_ONLY_TICKER:
        return {
            "ticker": ticker,
            "review_candidate_id": review_candidate_id_for(ticker),
            "company_name": DEFAULT_COMPANY_NAMES.get(ticker),
            "research_review_status": "repair_required_before_review",
            "review_action_status": "blocked",
            "source_phase": "phase39",
            "decision_confidence": "high",
            "pending_allowed": False,
            "paper_order_allowed": False,
            "promotion_allowed": False,
            "created_at": created,
            "updated_at": created,
            "last_reviewed_at": None,
            "metadata": {
                "repair_required_before_research_deepening": True,
                "research_deepening_allowed": False,
                "why_not_queue": ["evidence_chain_count remains 0", "repair required before review"],
            },
        }

    decision_payload = build_research_review_candidate_decision(conn, ticker)
    decision = decision_payload.get("research_review_decision") or {}
    boundary = decision.get("promotion_boundary") or {}
    status = str(decision.get("decision") or "unknown")
    if status not in RESEARCH_REVIEW_STATUSES:
        status = "unknown"
    lifecycle = {
        "ticker": ticker,
        "review_candidate_id": review_candidate_id_for(ticker),
        "company_name": DEFAULT_COMPANY_NAMES.get(ticker),
        "research_review_status": status,
        "review_action_status": "not_started" if status == "research_review_candidate" else "blocked",
        "source_phase": "phase39",
        "decision_confidence": decision.get("confidence"),
        "pending_allowed": bool(boundary.get("pending_allowed")),
        "paper_order_allowed": bool(boundary.get("paper_order_allowed")),
        "promotion_allowed": bool(boundary.get("promotion_allowed")),
        "created_at": created,
        "updated_at": created,
        "last_reviewed_at": None,
        "metadata": {
            "why_eligible": decision.get("why_eligible") or [],
            "why_not_ready": decision.get("why_not_ready") or [],
            "why_not_pending": decision.get("why_not_pending") or [],
            "human_review_questions": decision.get("human_review_questions") or [],
            "source_decision": status,
        },
    }
    validate_lifecycle_object(lifecycle)
    return lifecycle


def get_lifecycle(conn: sqlite3.Connection, review_candidate_id: str) -> dict[str, Any]:
    ensure_research_review_lifecycle_table(conn)
    row = conn.execute(
        """
        SELECT review_candidate_id, ticker, company_name, research_review_status,
               review_action_status, source_phase, decision_confidence,
               pending_allowed, paper_order_allowed, promotion_allowed,
               created_at, updated_at, last_reviewed_at, metadata_json
        FROM research_review_lifecycle
        WHERE review_candidate_id=?
        LIMIT 1
        """,
        (review_candidate_id,),
    ).fetchone()
    return _row_to_dict(row)


def get_lifecycle_by_ticker(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ensure_research_review_lifecycle_table(conn)
    row = conn.execute(
        """
        SELECT review_candidate_id, ticker, company_name, research_review_status,
               review_action_status, source_phase, decision_confidence,
               pending_allowed, paper_order_allowed, promotion_allowed,
               created_at, updated_at, last_reviewed_at, metadata_json
        FROM research_review_lifecycle
        WHERE ticker=?
        ORDER BY datetime(updated_at) DESC, review_candidate_id
        LIMIT 1
        """,
        (normalize_ticker(ticker),),
    ).fetchone()
    return _row_to_dict(row)


def upsert_lifecycle(conn: sqlite3.Connection, lifecycle: dict[str, Any]) -> dict[str, Any]:
    ensure_research_review_lifecycle_table(conn)
    validate_lifecycle_object(lifecycle)
    current = get_lifecycle(conn, str(lifecycle.get("review_candidate_id")))
    created_at = current.get("created_at") or lifecycle.get("created_at") or now_ts()
    updated_at = lifecycle.get("updated_at") or now_ts()
    conn.execute(
        """
        INSERT INTO research_review_lifecycle (
            review_candidate_id, ticker, company_name, research_review_status,
            review_action_status, source_phase, decision_confidence,
            pending_allowed, paper_order_allowed, promotion_allowed,
            created_at, updated_at, last_reviewed_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_candidate_id) DO UPDATE SET
            company_name=excluded.company_name,
            research_review_status=excluded.research_review_status,
            review_action_status=excluded.review_action_status,
            decision_confidence=excluded.decision_confidence,
            pending_allowed=excluded.pending_allowed,
            paper_order_allowed=excluded.paper_order_allowed,
            promotion_allowed=excluded.promotion_allowed,
            updated_at=excluded.updated_at,
            last_reviewed_at=excluded.last_reviewed_at,
            metadata_json=excluded.metadata_json
        """,
        (
            lifecycle.get("review_candidate_id"),
            normalize_ticker(lifecycle.get("ticker")),
            lifecycle.get("company_name"),
            lifecycle.get("research_review_status"),
            lifecycle.get("review_action_status"),
            lifecycle.get("source_phase") or "phase39",
            lifecycle.get("decision_confidence"),
            1 if lifecycle.get("pending_allowed") else 0,
            1 if lifecycle.get("paper_order_allowed") else 0,
            1 if lifecycle.get("promotion_allowed") else 0,
            created_at,
            updated_at,
            lifecycle.get("last_reviewed_at"),
            dumps_json(lifecycle.get("metadata") or {}),
        ),
    )
    return get_lifecycle(conn, str(lifecycle.get("review_candidate_id")))


def list_lifecycles(conn: sqlite3.Connection, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_research_review_lifecycle_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT review_candidate_id, ticker, company_name, research_review_status,
               review_action_status, source_phase, decision_confidence,
               pending_allowed, paper_order_allowed, promotion_allowed,
               created_at, updated_at, last_reviewed_at, metadata_json
        FROM research_review_lifecycle
        {where}
        ORDER BY datetime(updated_at) DESC, review_candidate_id
        """,
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def set_lifecycle_status(
    conn: sqlite3.Connection,
    *,
    review_candidate_id: str,
    research_review_status: str,
    review_action_status: str,
    metadata_updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = get_lifecycle(conn, review_candidate_id)
    if not current:
        raise ValueError(f"Unknown review lifecycle: {review_candidate_id}")
    validate_status_transition(str(current.get("research_review_status")), research_review_status)
    if review_action_status not in REVIEW_ACTION_STATUSES:
        raise ValueError(f"Unsupported review action status: {review_action_status}")
    metadata = {**(current.get("metadata") or {}), **(metadata_updates or {})}
    reviewed_at = now_ts()
    updated = {
        **current,
        "research_review_status": research_review_status,
        "review_action_status": review_action_status,
        "pending_allowed": False,
        "paper_order_allowed": False,
        "promotion_allowed": False,
        "updated_at": reviewed_at,
        "last_reviewed_at": reviewed_at,
        "metadata": metadata,
    }
    return upsert_lifecycle(conn, updated)
