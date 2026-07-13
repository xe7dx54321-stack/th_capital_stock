from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from smr_app.runtime.event_store import immediate_transaction, utc_now


ALLOWED_RELATIONS = frozenset({"supports", "contradicts", "supersedes", "context"})
ALLOWED_TRANSITIONS = {
    "candidate": {"approve": "approved", "reject": "rejected", "archive": "archived"},
    "approved": {"archive": "archived"},
    "rejected": {"archive": "archived"},
    "archived": {},
}


def _loads(raw: Any, fallback: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw or "")
    except (TypeError, ValueError):
        return fallback


def field_diff(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    diff = []
    for field in sorted(set(before) | set(after)):
        old = before.get(field)
        new = after.get(field)
        if old != new:
            diff.append({"field": field, "before": old, "after": new})
    return diff


def get_memory(conn: sqlite3.Connection, memory_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT memory_id, entity_type, entity_id, memory_type, content, status, confidence,
               source_run_id, valid_from, valid_until, last_verified_at, created_at, updated_at,
               parent_memory_id, version, field_diff_json, reviewed_by, review_reason, reviewed_at
        FROM memory_items WHERE memory_id=?
        """,
        (memory_id,),
    ).fetchone()
    if row is None:
        return None
    links = conn.execute(
        "SELECT evidence_id, relation, created_at FROM memory_evidence_links WHERE memory_id=? ORDER BY evidence_id, relation",
        (memory_id,),
    ).fetchall()
    logs = conn.execute(
        """SELECT review_id, action, previous_status, new_status, reviewer, reason, reviewed_at
           FROM memory_review_log WHERE memory_id=? ORDER BY reviewed_at DESC, review_id DESC""",
        (memory_id,),
    ).fetchall()
    return {
        "memory_id": row[0], "entity_type": row[1], "entity_id": row[2], "memory_type": row[3],
        "content": _loads(row[4], {}), "status": row[5], "confidence": row[6], "source_run_id": row[7],
        "valid_from": row[8], "valid_until": row[9], "last_verified_at": row[10], "created_at": row[11],
        "updated_at": row[12], "parent_memory_id": row[13], "version": int(row[14] or 1),
        "field_diff": _loads(row[15], []), "reviewed_by": row[16], "review_reason": row[17], "reviewed_at": row[18],
        "evidence_links": [{"evidence_id": item[0], "relation": item[1], "created_at": item[2]} for item in links],
        "review_log": [
            {"review_id": item[0], "action": item[1], "previous_status": item[2], "new_status": item[3],
             "reviewer": item[4], "reason": item[5], "reviewed_at": item[6]}
            for item in logs
        ],
    }


def current_approved(
    conn: sqlite3.Connection, entity_type: str, entity_id: str, memory_type: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        """SELECT memory_id FROM memory_items
           WHERE entity_type=? AND entity_id=? AND memory_type=? AND status='approved'
           ORDER BY version DESC, datetime(updated_at) DESC LIMIT 1""",
        (entity_type, entity_id, memory_type),
    ).fetchone()
    return get_memory(conn, row[0]) if row else None


def create_memory_candidate(
    conn: sqlite3.Connection, *, entity_type: str, entity_id: str, memory_type: str,
    content: dict[str, Any], evidence_links: list[dict[str, str]], source_run_id: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    if not entity_type.strip() or not entity_id.strip() or not memory_type.strip():
        raise ValueError("memory entity and type are required")
    if not isinstance(content, dict) or not content:
        raise ValueError("memory content must be a non-empty object")
    normalized_links = []
    for link in evidence_links:
        evidence_id = str(link.get("evidence_id") or "").strip()
        relation = str(link.get("relation") or "supports").strip()
        if not evidence_id or relation not in ALLOWED_RELATIONS:
            raise ValueError("invalid memory evidence link")
        normalized_links.append({"evidence_id": evidence_id, "relation": relation})

    approved = current_approved(conn, entity_type, entity_id, memory_type)
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) FROM memory_items WHERE entity_type=? AND entity_id=? AND memory_type=?",
        (entity_type, entity_id, memory_type),
    ).fetchone()
    version = int(row[0] or 0) + 1
    memory_id = f"memory_{uuid.uuid4().hex}"
    now = utc_now()
    diff = field_diff(approved["content"] if approved else {}, content)
    with immediate_transaction(conn):
        conn.execute(
            """
            INSERT INTO memory_items(
                memory_id, entity_type, entity_id, memory_type, content, status, confidence,
                source_run_id, created_at, updated_at, parent_memory_id, version, field_diff_json
            ) VALUES (?, ?, ?, ?, ?, 'candidate', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id, entity_type, entity_id, memory_type,
                json.dumps(content, ensure_ascii=False, sort_keys=True), confidence, source_run_id, now, now,
                approved["memory_id"] if approved else None, version,
                json.dumps(diff, ensure_ascii=False, sort_keys=True),
            ),
        )
        for link in normalized_links:
            conn.execute(
                "INSERT INTO memory_evidence_links(memory_id, evidence_id, relation, created_at) VALUES (?, ?, ?, ?)",
                (memory_id, link["evidence_id"], link["relation"], now),
            )
    return get_memory(conn, memory_id)  # type: ignore[return-value]


def review_memory(
    conn: sqlite3.Connection, memory_id: str, action: str, reviewer: str, reason: str,
) -> dict[str, Any]:
    memory = get_memory(conn, memory_id)
    if memory is None:
        raise KeyError(f"unknown memory: {memory_id}")
    reviewer = reviewer.strip()
    reason = reason.strip()
    if not reviewer or not reason:
        raise ValueError("reviewer and reason are required")
    new_status = ALLOWED_TRANSITIONS.get(memory["status"], {}).get(action)
    if not new_status:
        raise ValueError(f"action {action} is not allowed from {memory['status']}")
    now = utc_now()
    with immediate_transaction(conn):
        if action == "approve":
            previous = current_approved(conn, memory["entity_type"], memory["entity_id"], memory["memory_type"])
            if previous and previous["memory_id"] != memory_id:
                conn.execute(
                    "UPDATE memory_items SET status='archived', reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?",
                    (reviewer, reason, now, now, previous["memory_id"]),
                )
                conn.execute(
                    "INSERT INTO memory_review_log VALUES (?, ?, 'supersede', 'approved', 'archived', ?, ?, ?)",
                    (f"review_{uuid.uuid4().hex}", previous["memory_id"], reviewer, reason, now),
                )
        conn.execute(
            "UPDATE memory_items SET status=?, reviewed_by=?, review_reason=?, reviewed_at=?, updated_at=? WHERE memory_id=?",
            (new_status, reviewer, reason, now, now, memory_id),
        )
        conn.execute(
            "INSERT INTO memory_review_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"review_{uuid.uuid4().hex}", memory_id, action, memory["status"], new_status, reviewer, reason, now),
        )
    return get_memory(conn, memory_id)  # type: ignore[return-value]
