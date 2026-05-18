#!/usr/bin/env python3
"""Resolve manual review decisions for SMR Wiki ingest drafts."""

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
    draft_registry_status,
    dumps_json,
    ensure_import_execution_table,
    ensure_ingest_draft_table,
    generate_execution_id,
    validate_review_reason_code,
)

DB_PATH = project_path("01_data", "db", "smr.db")


def load_draft(conn, draft_id):
    row = conn.execute(
        """
        SELECT draft_id, source_id, governance_status, approval_status, review_reason_code, review_reason
        FROM smr_wiki_ingest_draft
        WHERE draft_id=?
        """,
        (draft_id,),
    ).fetchone()
    if not row:
        raise SystemExit(f"Draft not found: {draft_id}")
    return {
        "draft_id": row[0],
        "source_id": row[1],
        "governance_status": row[2],
        "approval_status": row[3],
        "review_reason_code": row[4],
        "review_reason": row[5],
    }


def resolve_state(draft, decision, reason_code, reason):
    if decision == "approved":
        if draft["review_reason_code"] == "duplicate_source":
            raise SystemExit("duplicate_source draft cannot be approved for import")
        return ("ready", "approved", None, reason or None)

    if decision == "rejected":
        if not reason_code:
            raise SystemExit("Rejected review requires --reason-code")
        return ("blocked", "rejected", reason_code, reason or "Rejected during manual review.")

    if decision == "reopened":
        if draft["approval_status"] != "rejected":
            raise SystemExit("Only rejected drafts can be reopened")
        return ("review_required", "reopened", reason_code or "needs_human_judgement", reason or "Reopened for reevaluation.")

    raise SystemExit(f"Unsupported decision: {decision}")


def resolve_review_decision(
    conn,
    draft_id,
    decision,
    reason_code=None,
    reason=None,
    source="resolve_review.py",
):
    ensure_ingest_draft_table(conn)
    ensure_import_execution_table(conn)

    normalized_reason_code = validate_review_reason_code(reason_code)
    draft = load_draft(conn, draft_id)
    governance_status, approval_status, review_reason_code, review_reason = resolve_state(
        draft,
        decision,
        normalized_reason_code,
        reason,
    )

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
        (
            governance_status,
            approval_status,
            review_reason_code,
            review_reason,
            draft_id,
        ),
    )

    execution_id = generate_execution_id("review_resolution")
    conn.execute(
        """
        INSERT INTO smr_wiki_import_execution (
            execution_id,
            draft_id,
            source_id,
            mode,
            operation,
            status,
            knowledge_id,
            target_rel_path,
            details_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """,
        (
            execution_id,
            draft["draft_id"],
            draft["source_id"],
            "review_resolution",
            decision,
            decision,
            None,
            None,
            dumps_json(
                {
                    "review_reason_code": review_reason_code,
                    "review_reason": review_reason,
                    "previous_governance_status": draft["governance_status"],
                    "previous_approval_status": draft["approval_status"],
                }
            ),
        ),
    )
    register_snapshot(
        conn,
        entity_type="wiki_draft",
        entity_id=draft["draft_id"],
        status=draft_registry_status(governance_status, approval_status, review_reason_code),
        source=source,
        relationships={
            "source_id": draft["source_id"],
            "review_execution_id": execution_id,
        },
        payload={
            "decision": decision,
            "governance_status": governance_status,
            "approval_status": approval_status,
            "review_reason_code": review_reason_code,
            "review_reason": review_reason,
            "previous_governance_status": draft["governance_status"],
            "previous_approval_status": draft["approval_status"],
        },
    )
    return {
        "draft_id": draft["draft_id"],
        "decision": decision,
        "governance_status": governance_status,
        "approval_status": approval_status,
        "review_reason_code": review_reason_code,
        "review_reason": review_reason,
        "review_execution_id": execution_id,
        "source_id": draft["source_id"],
    }


def main():
    parser = argparse.ArgumentParser(description="Resolve SMR Wiki review decision")
    parser.add_argument("--draft-id", required=True, help="Draft id to resolve")
    parser.add_argument("--decision", required=True, choices=["approved", "rejected", "reopened"])
    parser.add_argument("--reason-code", help="Structured review reason code")
    parser.add_argument("--reason", help="Free-form review note")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    result = resolve_review_decision(
        conn,
        draft_id=args.draft_id,
        decision=args.decision,
        reason_code=args.reason_code,
        reason=args.reason,
    )
    conn.commit()
    conn.close()

    log_run(
        "resolve_review.py",
        "success",
        "review decision resolved",
        {
            "draft_id": result["draft_id"],
            "decision": args.decision,
            "governance_status": result["governance_status"],
            "approval_status": result["approval_status"],
        },
    )
    print(f"Resolved {result['draft_id']} -> decision={args.decision}")
    print(f"  governance_status={result['governance_status']}")
    print(f"  approval_status={result['approval_status']}")


if __name__ == "__main__":
    main()
