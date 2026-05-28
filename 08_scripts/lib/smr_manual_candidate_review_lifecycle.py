#!/usr/bin/env python3
"""Phase 44 manual candidate review lifecycle."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_manual_intake_candidate_generator import (
    CONFIRMATION_STATUS,
    FINAL_ALLOWED_USAGE,
    build_candidate_generation_payload,
    list_manual_intake_candidates,
    write_manual_intake_candidates,
)
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


LIFECYCLE_STATUSES = {
    "manual_candidate_created",
    "manual_candidate_in_review",
    "manual_candidate_accepted",
    "manual_candidate_rejected",
    "manual_candidate_downgraded",
    "manual_candidate_scenario_only",
    "manual_candidate_proxy_only",
    "manual_candidate_needs_better_source",
    "manual_candidate_archived",
    "unknown",
}

CANDIDATE_TYPE_ALIASES = {
    "official_consensus": "official_consensus",
    "official_consensus_candidate": "official_consensus",
    "supplier_share": "supplier_share",
    "supplier_share_scenario": "supplier_share",
    "customer_allocation": "customer_allocation",
    "confirmed_customer_allocation": "customer_allocation",
    "customer_allocation_proxy": "customer_allocation",
}

EVIDENCE_TYPE_BY_CANDIDATE_TYPE = {
    "official_consensus": "official_consensus",
    "supplier_share": "supplier_share",
    "customer_allocation": "confirmed_customer_allocation",
}

VARIABLE_TYPE_BY_CANDIDATE_TYPE = {
    "official_consensus": "official_consensus_candidate",
    "supplier_share": "supplier_share_scenario",
    "customer_allocation": "customer_allocation_proxy",
}

DEFAULT_ACTION_BY_CANDIDATE_TYPE = {
    "official_consensus": "accept_as_candidate",
    "supplier_share": "mark_as_scenario_only",
    "customer_allocation": "mark_as_proxy_only",
}

STATUS_BY_ACTION = {
    "accept_as_candidate": "manual_candidate_accepted",
    "reject_manual_candidate": "manual_candidate_rejected",
    "downgrade_usage": "manual_candidate_downgraded",
    "request_better_source": "manual_candidate_needs_better_source",
    "mark_as_scenario_only": "manual_candidate_scenario_only",
    "mark_as_proxy_only": "manual_candidate_proxy_only",
    "archive_candidate": "manual_candidate_archived",
}

FINAL_LIMITATIONS_BY_CANDIDATE_TYPE = {
    "official_consensus": [
        "candidate only",
        "requires human verification before use as benchmark",
        "not confirmed official consensus",
    ],
    "supplier_share": [
        "not a fact",
        "scenario analysis only",
        "not usable for promotion",
    ],
    "customer_allocation": [
        "proxy only",
        "not confirmed allocation",
        "not usable for promotion",
    ],
}


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: Any, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def canonical_candidate_type(candidate_type: str) -> str:
    key = str(candidate_type or "").strip()
    if key not in CANDIDATE_TYPE_ALIASES:
        raise ValueError(f"Unsupported manual candidate type: {candidate_type}")
    return CANDIDATE_TYPE_ALIASES[key]


def candidate_type_for_candidate(candidate: dict[str, Any]) -> str:
    variable_type = str(candidate.get("variable_type") or "")
    evidence_type = str(candidate.get("evidence_type") or "")
    for candidate_type, expected in VARIABLE_TYPE_BY_CANDIDATE_TYPE.items():
        if variable_type == expected:
            return candidate_type
    if evidence_type == "confirmed_customer_allocation":
        return "customer_allocation"
    return canonical_candidate_type(evidence_type)


def ensure_manual_candidate_lifecycle_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_candidate_review_lifecycle (
            candidate_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            candidate_type TEXT NOT NULL,
            status TEXT NOT NULL,
            confirmation_status TEXT NOT NULL,
            allowed_usage TEXT NOT NULL,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            pending_allowed INTEGER NOT NULL DEFAULT 0,
            paper_order_allowed INTEGER NOT NULL DEFAULT 0,
            last_action TEXT,
            limitations_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_manual_candidate_lifecycle_ticker
        ON manual_candidate_review_lifecycle(ticker, candidate_type, updated_at DESC)
        """
    )


def _candidate_sample_for_type(candidate_type: str) -> str:
    return {
        "official_consensus": "official_consensus_authorized_sample",
        "supplier_share": "supplier_share_scenario_sample",
        "customer_allocation": "customer_allocation_proxy_sample",
    }[candidate_type]


def _find_candidate(rows: list[dict[str, Any]], candidate_type: str) -> dict[str, Any] | None:
    evidence_type = EVIDENCE_TYPE_BY_CANDIDATE_TYPE[candidate_type]
    variable_type = VARIABLE_TYPE_BY_CANDIDATE_TYPE[candidate_type]
    for row in rows:
        if row.get("evidence_type") == evidence_type or row.get("variable_type") == variable_type:
            return row
    return None


def load_or_build_candidate(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    candidate_type: str = "official_consensus",
    materialize: bool = False,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    canonical = canonical_candidate_type(candidate_type)
    rows = list_manual_intake_candidates(conn, ticker=ticker)
    candidate = _find_candidate(rows, canonical)
    if candidate:
        return candidate

    generated = build_candidate_generation_payload(
        None,
        ticker=ticker,
        sample=_candidate_sample_for_type(canonical),
        mode="dry_run",
    )
    candidate_rows = (generated.get("manual_intake_candidate_generation") or {}).get("candidate_rows") or []
    candidate = candidate_rows[0] if candidate_rows else None
    if not candidate:
        raise ValueError(f"Manual candidate not available for {ticker} / {canonical}")
    if materialize:
        write_manual_intake_candidates(conn, [candidate], mark_persisted=True)
        rows = list_manual_intake_candidates(conn, ticker=ticker)
        candidate = _find_candidate(rows, canonical) or candidate
    return candidate


def _row_to_lifecycle(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "candidate_id": row[0],
        "ticker": row[1],
        "candidate_type": row[2],
        "status": row[3],
        "confirmation_status": row[4],
        "allowed_usage": row[5],
        "usable_for_promotion": bool(row[6]),
        "pending_allowed": bool(row[7]),
        "paper_order_allowed": bool(row[8]),
        "last_action": row[9],
        "limitations": loads_json(row[10], []),
        "metadata": loads_json(row[11], {}),
        "created_at": row[12],
        "updated_at": row[13],
    }


def load_lifecycle(conn: sqlite3.Connection, candidate_id: str) -> dict[str, Any] | None:
    ensure_manual_candidate_lifecycle_table(conn)
    row = conn.execute(
        """
        SELECT candidate_id, ticker, candidate_type, status, confirmation_status,
               allowed_usage, usable_for_promotion, pending_allowed, paper_order_allowed,
               last_action, limitations_json, metadata_json, created_at, updated_at
        FROM manual_candidate_review_lifecycle
        WHERE candidate_id=?
        LIMIT 1
        """,
        (candidate_id,),
    ).fetchone()
    return _row_to_lifecycle(row) if row else None


def list_lifecycles(conn: sqlite3.Connection, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_manual_candidate_lifecycle_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT candidate_id, ticker, candidate_type, status, confirmation_status,
               allowed_usage, usable_for_promotion, pending_allowed, paper_order_allowed,
               last_action, limitations_json, metadata_json, created_at, updated_at
        FROM manual_candidate_review_lifecycle
        {where}
        ORDER BY ticker, candidate_type, candidate_id
        """,
        params,
    ).fetchall()
    return [_row_to_lifecycle(row) for row in rows]


def lifecycle_from_candidate(
    candidate: dict[str, Any],
    *,
    status: str = "manual_candidate_created",
    action: str | None = None,
) -> dict[str, Any]:
    candidate_type = candidate_type_for_candidate(candidate)
    if status not in LIFECYCLE_STATUSES:
        status = "unknown"
    limitations = list(dict.fromkeys((candidate.get("limitations") or []) + FINAL_LIMITATIONS_BY_CANDIDATE_TYPE.get(candidate_type, [])))
    evidence_type = EVIDENCE_TYPE_BY_CANDIDATE_TYPE[candidate_type]
    return {
        "ticker": normalize_ticker(str(candidate.get("ticker") or TARGET_REVIEW_TICKER)),
        "candidate_id": candidate.get("candidate_id"),
        "candidate_type": candidate_type,
        "before_status": "manual_candidate_created",
        "after_status": status,
        "status": status,
        "confirmation_status": CONFIRMATION_STATUS.get(evidence_type, candidate.get("confirmation_status") or "candidate_not_confirmed"),
        "allowed_usage": FINAL_ALLOWED_USAGE.get(evidence_type, candidate.get("allowed_usage")),
        "usable_for_promotion": False,
        "pending_allowed": False,
        "paper_order_allowed": False,
        "last_action": action,
        "limitations": limitations,
        "metadata": {
            "accepted_is_not_confirmed": True,
            "scenario_only_is_not_fact": candidate_type == "supplier_share",
            "proxy_only_is_not_confirmed_allocation": candidate_type == "customer_allocation",
            "promotion_gate_connected": False,
        },
    }


def validate_transition(before_status: str | None, after_status: str) -> tuple[bool, str]:
    before = before_status if before_status in LIFECYCLE_STATUSES else "manual_candidate_created"
    if after_status not in LIFECYCLE_STATUSES:
        return False, f"invalid lifecycle status: {after_status}"
    if after_status in {"unknown", "manual_candidate_in_review", "manual_candidate_created"}:
        return True, "allowed"
    if before == "manual_candidate_archived" and after_status != "manual_candidate_archived":
        return False, "archived manual candidate cannot be reopened in Phase 44"
    return True, "allowed"


def upsert_lifecycle(conn: sqlite3.Connection, lifecycle: dict[str, Any]) -> dict[str, Any]:
    ensure_manual_candidate_lifecycle_table(conn)
    now = now_ts()
    existing = load_lifecycle(conn, str(lifecycle.get("candidate_id")))
    created_at = (existing or {}).get("created_at") or now
    before = (existing or {}).get("status") or "manual_candidate_created"
    after = lifecycle.get("after_status") or lifecycle.get("status")
    ok, reason = validate_transition(before, str(after))
    if not ok:
        raise ValueError(reason)
    conn.execute(
        """
        INSERT INTO manual_candidate_review_lifecycle (
            candidate_id, ticker, candidate_type, status, confirmation_status,
            allowed_usage, usable_for_promotion, pending_allowed, paper_order_allowed,
            last_action, limitations_json, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(candidate_id) DO UPDATE SET
            ticker=excluded.ticker,
            candidate_type=excluded.candidate_type,
            status=excluded.status,
            confirmation_status=excluded.confirmation_status,
            allowed_usage=excluded.allowed_usage,
            usable_for_promotion=0,
            pending_allowed=0,
            paper_order_allowed=0,
            last_action=excluded.last_action,
            limitations_json=excluded.limitations_json,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            lifecycle.get("candidate_id"),
            lifecycle.get("ticker"),
            lifecycle.get("candidate_type"),
            after,
            lifecycle.get("confirmation_status"),
            lifecycle.get("allowed_usage"),
            0,
            0,
            0,
            lifecycle.get("last_action"),
            dumps_json(lifecycle.get("limitations") or []),
            dumps_json(lifecycle.get("metadata") or {}),
            created_at,
            now,
        ),
    )
    updated = load_lifecycle(conn, str(lifecycle.get("candidate_id"))) or {}
    updated["before_status"] = before
    updated["after_status"] = after
    return updated
