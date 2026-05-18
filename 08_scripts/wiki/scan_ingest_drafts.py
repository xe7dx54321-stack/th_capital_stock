#!/usr/bin/env python3
"""Scan SMR Wiki ingest drafts for duplicate and governance signals."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import (
    SINGLETON_CATEGORIES,
    active_knowledge_entry,
    draft_registry_status,
    ensure_import_execution_table,
    ensure_ingest_draft_table,
    ensure_knowledge_index_table,
    imported_source_exists,
    knowledge_id_for,
)

DB_PATH = project_path("01_data", "db", "smr.db")


def load_drafts(conn, limit):
    rows = conn.execute(
        """
        SELECT
            draft_id,
            source_id,
            draft_type,
            entity_type,
            entity_id,
            title,
            candidate_category,
            governance_status,
            approval_status,
            review_reason_code,
            review_reason
        FROM smr_wiki_ingest_draft
        ORDER BY datetime(updated_at) DESC, draft_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "draft_id": row[0],
            "source_id": row[1],
            "draft_type": row[2],
            "entity_type": row[3],
            "entity_id": row[4],
            "title": row[5],
            "candidate_category": row[6],
            "governance_status": row[7],
            "approval_status": row[8],
            "review_reason_code": row[9],
            "review_reason": row[10],
        }
        for row in rows
    ]


def classify_draft(conn, draft):
    current = (
        draft["governance_status"],
        draft["approval_status"],
        draft["review_reason_code"],
        draft["review_reason"],
    )

    if imported_source_exists(conn, draft["source_id"]):
        return (
            "blocked",
            draft["approval_status"],
            "duplicate_source",
            "该 source 已经导入过正式 Wiki，不应重复导入。",
        )

    if draft["approval_status"] == "rejected":
        return current

    knowledge_id = knowledge_id_for(
        draft["candidate_category"],
        draft["entity_id"],
        source_id=draft["source_id"],
    )
    existing = active_knowledge_entry(conn, knowledge_id)

    if (
        draft["candidate_category"] in SINGLETON_CATEGORIES
        and existing
        and existing["source_id"] != draft["source_id"]
        and draft["approval_status"] not in {"approved", "auto_ready"}
    ):
        return (
            "review_required",
            draft["approval_status"] if draft["approval_status"] == "reopened" else "pending_manual_review",
            "duplicate_thesis",
            "目标知识页已存在，导入会覆盖当前页面，需要人工确认。",
        )

    return current


def update_draft(conn, draft_id, classification):
    governance_status, approval_status, reason_code, reason = classification
    conn.execute(
        """
        UPDATE smr_wiki_ingest_draft
        SET governance_status=?,
            approval_status=?,
            review_reason_code=?,
            review_reason=?,
            updated_at=datetime('now', 'localtime')
        WHERE draft_id=?
        """,
        (governance_status, approval_status, reason_code, reason, draft_id),
    )


def main():
    parser = argparse.ArgumentParser(description="Scan SMR Wiki ingest drafts")
    parser.add_argument("--limit", type=int, default=200, help="Maximum drafts to scan")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_ingest_draft_table(conn)
    ensure_knowledge_index_table(conn)
    ensure_import_execution_table(conn)

    drafts = load_drafts(conn, args.limit)
    updated = 0
    counts = {}
    for draft in drafts:
        classification = classify_draft(conn, draft)
        update_draft(conn, draft["draft_id"], classification)
        register_snapshot(
            conn,
            entity_type="wiki_draft",
            entity_id=draft["draft_id"],
            status=draft_registry_status(classification[0], classification[1], classification[2]),
            source="scan_ingest_drafts.py",
            relationships={
                "source_id": draft["source_id"],
                "draft_type": draft["draft_type"],
                "entity_type": draft["entity_type"],
                "entity_id": draft["entity_id"],
                "candidate_category": draft["candidate_category"],
            },
            payload={
                "approval_status": classification[1],
                "review_reason_code": classification[2],
                "review_reason": classification[3],
                "title": draft["title"],
            },
        )
        counts[classification[0]] = counts.get(classification[0], 0) + 1
        updated += 1

    register_snapshot(
        conn,
        entity_type="ingest_draft_scan",
        entity_id="all_drafts",
        status="scanned" if updated else "empty",
        source="scan_ingest_drafts.py",
        relationships={"limit": args.limit},
        payload={
            "draft_count": updated,
            "counts_by_governance_status": counts,
        },
    )

    conn.commit()
    conn.close()

    log_run(
        "scan_ingest_drafts.py",
        "success",
        "ingest drafts scanned",
        {"draft_count": updated, "counts_by_governance_status": counts},
    )
    print(f"Scanned drafts: {updated}")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
