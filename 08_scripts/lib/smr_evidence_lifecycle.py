#!/usr/bin/env python3
"""Evidence lifecycle state helpers for Phase 31 governance."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table
from smr_wiki import now_ts


LIFECYCLE_STATUSES = {
    "persisted_candidate",
    "pending_review",
    "approved_evidence",
    "rejected_evidence",
    "downgraded_evidence",
    "marked_noise",
    "needs_better_source",
    "linked_to_variable_pack",
    "archived",
    "removed",
    "unknown",
}

REVIEW_STATUSES = {
    "not_required",
    "review_required",
    "reviewed",
    "needs_follow_up",
    "blocked",
}

ALLOWED_USAGES_ORDER = {
    "blocked": 0,
    "planned_only": 1,
    "context_only": 2,
    "scenario_analysis_only": 3,
    "valuation_support": 4,
    "research_evidence": 5,
}

DEFAULT_ALLOWED_USAGE = "scenario_analysis_only"


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


def ensure_evidence_lifecycle_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_lifecycle_state (
            evidence_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            variable_type TEXT,
            lifecycle_status TEXT NOT NULL,
            review_status TEXT NOT NULL,
            quality_score INTEGER,
            quality_bucket TEXT,
            allowed_usage TEXT NOT NULL,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            source_id TEXT,
            source_url TEXT,
            chunk_id TEXT,
            quoted_span_preview TEXT,
            limitations_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_reviewed_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_evidence_lifecycle_status
        ON evidence_lifecycle_state(lifecycle_status, review_status, updated_at DESC)
        """
    )


def _quality_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = loads_json(candidate.get("payload_json"), {}) if "payload_json" in candidate else candidate.get("payload") or {}
    quality = candidate.get("quality") or payload.get("quality") or {}
    return quality if isinstance(quality, dict) else {}


def _limitations_from_candidate(candidate: dict[str, Any]) -> list[Any]:
    if "limitations_json" in candidate:
        return loads_json(candidate.get("limitations_json"), [])
    return list(candidate.get("limitations") or [])


def _preview(text: str | None, limit: int = 240) -> str:
    compact = " ".join(str(text or "").split())
    return compact[:limit]


def lifecycle_from_candidate(
    candidate: dict[str, Any],
    *,
    lifecycle_status: str | None = None,
    review_status: str | None = None,
) -> dict[str, Any]:
    quality = _quality_from_candidate(candidate)
    bucket = quality.get("quality_bucket") or candidate.get("quality_bucket")
    score = quality.get("quality_score", candidate.get("quality_score"))
    inferred_review = "review_required" if bucket in {"review_required", "weak_but_usable"} else "not_required"
    inferred_lifecycle = "pending_review" if inferred_review == "review_required" else "persisted_candidate"
    status = lifecycle_status or inferred_lifecycle
    review = review_status or inferred_review
    if status not in LIFECYCLE_STATUSES:
        status = "unknown"
    if review not in REVIEW_STATUSES:
        review = "blocked"
    return {
        "evidence_id": candidate.get("evidence_id"),
        "ticker": candidate.get("ticker"),
        "variable_type": candidate.get("variable_type"),
        "lifecycle_status": status,
        "review_status": review,
        "quality_score": int(score) if str(score or "").isdigit() else score,
        "quality_bucket": bucket,
        "allowed_usage": candidate.get("allowed_usage") or DEFAULT_ALLOWED_USAGE,
        "usable_for_promotion": False,
        "source_id": candidate.get("source_id"),
        "source_url": candidate.get("source_url"),
        "chunk_id": candidate.get("chunk_id"),
        "quoted_span": candidate.get("quoted_span"),
        "quoted_span_preview": _preview(candidate.get("quoted_span")),
        "limitations": _limitations_from_candidate(candidate),
        "metadata": {
            "source_type": candidate.get("source_type"),
            "claim_text": candidate.get("claim_text"),
            "evidence_status": candidate.get("evidence_status"),
            "phase": 31,
            "approved_is_not_promotion": True,
        },
        "created_at": candidate.get("created_at"),
        "last_reviewed_at": None,
    }


def validate_lifecycle_object(item: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not item.get("evidence_id"):
        issues.append({"severity": "error", "path": "evidence_id", "message": "evidence_id is required"})
    if item.get("lifecycle_status") not in LIFECYCLE_STATUSES:
        issues.append({"severity": "error", "path": "lifecycle_status", "message": "invalid lifecycle status"})
    if item.get("review_status") not in REVIEW_STATUSES:
        issues.append({"severity": "error", "path": "review_status", "message": "invalid review status"})
    if bool(item.get("usable_for_promotion")):
        issues.append({"severity": "error", "path": "usable_for_promotion", "message": "Phase 31 lifecycle cannot enable promotion"})
    return issues


ALLOWED_TRANSITIONS = {
    "unknown": set(LIFECYCLE_STATUSES),
    "persisted_candidate": {
        "persisted_candidate",
        "pending_review",
        "approved_evidence",
        "rejected_evidence",
        "downgraded_evidence",
        "marked_noise",
        "needs_better_source",
        "linked_to_variable_pack",
        "archived",
    },
    "pending_review": {
        "pending_review",
        "approved_evidence",
        "rejected_evidence",
        "downgraded_evidence",
        "marked_noise",
        "needs_better_source",
        "archived",
    },
    "approved_evidence": {
        "approved_evidence",
        "downgraded_evidence",
        "marked_noise",
        "needs_better_source",
        "linked_to_variable_pack",
        "archived",
    },
    "rejected_evidence": {"rejected_evidence", "needs_better_source", "archived"},
    "downgraded_evidence": {"downgraded_evidence", "marked_noise", "needs_better_source", "archived"},
    "marked_noise": {"marked_noise", "archived"},
    "needs_better_source": {"needs_better_source", "pending_review", "archived"},
    "linked_to_variable_pack": {
        "linked_to_variable_pack",
        "approved_evidence",
        "downgraded_evidence",
        "marked_noise",
        "archived",
    },
    "archived": {"archived"},
    "removed": {"removed", "archived"},
}


def validate_status_transition(before_status: str | None, after_status: str) -> tuple[bool, str]:
    before = before_status if before_status in LIFECYCLE_STATUSES else "unknown"
    if after_status not in LIFECYCLE_STATUSES:
        return False, f"invalid lifecycle status: {after_status}"
    if after_status not in ALLOWED_TRANSITIONS.get(before, set()):
        return False, f"transition {before}->{after_status} is not allowed"
    return True, "allowed"


def load_semantic_evidence_candidate(conn: sqlite3.Connection, evidence_id: str) -> dict[str, Any] | None:
    ensure_semantic_evidence_candidate_table(conn)
    row = conn.execute(
        """
        SELECT evidence_id, ticker, theme, source_id, source_url, source_type, chunk_id,
               quoted_span, variable_type, claim_text, evidence_status, allowed_usage,
               usable_for_expectation_gap, usable_for_valuation_support, usable_for_promotion,
               limitations_json, payload_json, created_at, updated_at
        FROM semantic_evidence_candidates
        WHERE evidence_id = ?
        LIMIT 1
        """,
        (evidence_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "evidence_id": row[0],
        "ticker": row[1],
        "theme": row[2],
        "source_id": row[3],
        "source_url": row[4],
        "source_type": row[5],
        "chunk_id": row[6],
        "quoted_span": row[7],
        "variable_type": row[8],
        "claim_text": row[9],
        "evidence_status": row[10],
        "allowed_usage": row[11],
        "usable_for_expectation_gap": bool(row[12]),
        "usable_for_valuation_support": bool(row[13]),
        "usable_for_promotion": bool(row[14]),
        "limitations": loads_json(row[15], []),
        "payload": loads_json(row[16], {}),
        "created_at": row[17],
        "updated_at": row[18],
    }


def list_semantic_evidence_candidates(conn: sqlite3.Connection, *, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_semantic_evidence_candidate_table(conn)
    where = "WHERE ticker = ?" if ticker else ""
    params: tuple[Any, ...] = (ticker,) if ticker else ()
    rows = conn.execute(
        f"""
        SELECT evidence_id, ticker, theme, source_id, source_url, source_type, chunk_id,
               quoted_span, variable_type, claim_text, evidence_status, allowed_usage,
               usable_for_expectation_gap, usable_for_valuation_support, usable_for_promotion,
               limitations_json, payload_json, created_at, updated_at
        FROM semantic_evidence_candidates
        {where}
        ORDER BY ticker, updated_at DESC, evidence_id
        """,
        params,
    ).fetchall()
    return [
        {
            "evidence_id": row[0],
            "ticker": row[1],
            "theme": row[2],
            "source_id": row[3],
            "source_url": row[4],
            "source_type": row[5],
            "chunk_id": row[6],
            "quoted_span": row[7],
            "variable_type": row[8],
            "claim_text": row[9],
            "evidence_status": row[10],
            "allowed_usage": row[11],
            "usable_for_expectation_gap": bool(row[12]),
            "usable_for_valuation_support": bool(row[13]),
            "usable_for_promotion": bool(row[14]),
            "limitations": loads_json(row[15], []),
            "payload": loads_json(row[16], {}),
            "created_at": row[17],
            "updated_at": row[18],
        }
        for row in rows
    ]


def upsert_lifecycle_state(conn: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    ensure_evidence_lifecycle_table(conn)
    issues = validate_lifecycle_object(item)
    if any(issue.get("severity") == "error" for issue in issues):
        raise ValueError(f"invalid lifecycle object: {issues}")
    now = now_ts()
    created_at = item.get("created_at") or now
    conn.execute(
        """
        INSERT INTO evidence_lifecycle_state (
            evidence_id, ticker, variable_type, lifecycle_status, review_status,
            quality_score, quality_bucket, allowed_usage, usable_for_promotion,
            source_id, source_url, chunk_id, quoted_span_preview, limitations_json,
            metadata_json, created_at, updated_at, last_reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            ticker=excluded.ticker,
            variable_type=excluded.variable_type,
            lifecycle_status=excluded.lifecycle_status,
            review_status=excluded.review_status,
            quality_score=excluded.quality_score,
            quality_bucket=excluded.quality_bucket,
            allowed_usage=excluded.allowed_usage,
            usable_for_promotion=0,
            source_id=excluded.source_id,
            source_url=excluded.source_url,
            chunk_id=excluded.chunk_id,
            quoted_span_preview=excluded.quoted_span_preview,
            limitations_json=excluded.limitations_json,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at,
            last_reviewed_at=excluded.last_reviewed_at
        """,
        (
            item.get("evidence_id"),
            item.get("ticker"),
            item.get("variable_type"),
            item.get("lifecycle_status"),
            item.get("review_status"),
            item.get("quality_score"),
            item.get("quality_bucket"),
            item.get("allowed_usage") or DEFAULT_ALLOWED_USAGE,
            item.get("source_id"),
            item.get("source_url"),
            item.get("chunk_id"),
            item.get("quoted_span_preview") or _preview(item.get("quoted_span")),
            dumps_json(item.get("limitations") or []),
            dumps_json(item.get("metadata") or {}),
            created_at,
            now,
            item.get("last_reviewed_at"),
        ),
    )
    return get_lifecycle_state(conn, str(item.get("evidence_id")))


def get_lifecycle_state(conn: sqlite3.Connection, evidence_id: str) -> dict[str, Any] | None:
    ensure_evidence_lifecycle_table(conn)
    row = conn.execute(
        """
        SELECT evidence_id, ticker, variable_type, lifecycle_status, review_status,
               quality_score, quality_bucket, allowed_usage, usable_for_promotion,
               source_id, source_url, chunk_id, quoted_span_preview, limitations_json,
               metadata_json, created_at, updated_at, last_reviewed_at
        FROM evidence_lifecycle_state
        WHERE evidence_id = ?
        LIMIT 1
        """,
        (evidence_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "evidence_id": row[0],
        "ticker": row[1],
        "variable_type": row[2],
        "lifecycle_status": row[3],
        "review_status": row[4],
        "quality_score": row[5],
        "quality_bucket": row[6],
        "allowed_usage": row[7],
        "usable_for_promotion": bool(row[8]),
        "source_id": row[9],
        "source_url": row[10],
        "chunk_id": row[11],
        "quoted_span_preview": row[12],
        "limitations": loads_json(row[13], []),
        "metadata": loads_json(row[14], {}),
        "created_at": row[15],
        "updated_at": row[16],
        "last_reviewed_at": row[17],
    }


def list_lifecycle_states(conn: sqlite3.Connection, *, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_evidence_lifecycle_table(conn)
    where = "WHERE ticker = ?" if ticker else ""
    params: tuple[Any, ...] = (ticker,) if ticker else ()
    rows = conn.execute(
        f"""
        SELECT evidence_id, ticker, variable_type, lifecycle_status, review_status,
               quality_score, quality_bucket, allowed_usage, usable_for_promotion,
               source_id, source_url, chunk_id, quoted_span_preview, limitations_json,
               metadata_json, created_at, updated_at, last_reviewed_at
        FROM evidence_lifecycle_state
        {where}
        ORDER BY ticker, updated_at DESC, evidence_id
        """,
        params,
    ).fetchall()
    return [
        {
            "evidence_id": row[0],
            "ticker": row[1],
            "variable_type": row[2],
            "lifecycle_status": row[3],
            "review_status": row[4],
            "quality_score": row[5],
            "quality_bucket": row[6],
            "allowed_usage": row[7],
            "usable_for_promotion": bool(row[8]),
            "source_id": row[9],
            "source_url": row[10],
            "chunk_id": row[11],
            "quoted_span_preview": row[12],
            "limitations": loads_json(row[13], []),
            "metadata": loads_json(row[14], {}),
            "created_at": row[15],
            "updated_at": row[16],
            "last_reviewed_at": row[17],
        }
        for row in rows
    ]


def ensure_lifecycle_for_persisted_candidates(conn: sqlite3.Connection, *, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_evidence_lifecycle_table(conn)
    states = []
    for candidate in list_semantic_evidence_candidates(conn, ticker=ticker):
        current = get_lifecycle_state(conn, str(candidate.get("evidence_id")))
        if current:
            states.append(current)
            continue
        states.append(upsert_lifecycle_state(conn, lifecycle_from_candidate(candidate)))
    return states


def usage_rank(usage: str | None) -> int:
    return ALLOWED_USAGES_ORDER.get(str(usage or ""), -1)


def downgrade_allowed_usage(current_usage: str | None, target_usage: str) -> tuple[bool, str]:
    if target_usage not in ALLOWED_USAGES_ORDER:
        return False, f"invalid target usage: {target_usage}"
    if usage_rank(target_usage) > usage_rank(current_usage):
        return False, "downgrade_usage cannot increase allowed_usage"
    return True, "allowed"
