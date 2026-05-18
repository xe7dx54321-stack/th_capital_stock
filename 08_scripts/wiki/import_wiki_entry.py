#!/usr/bin/env python3
"""Import an approved SMR Wiki ingest draft into the formal wiki layer."""

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
    dumps_json,
    ensure_import_execution_table,
    ensure_ingest_draft_table,
    ensure_knowledge_index_table,
    generate_execution_id,
    imported_source_exists,
    knowledge_id_for,
    loads_json,
    now_ts,
    page_type_for_category,
    wiki_abs_path_for,
    wiki_rel_path_for,
)

DB_PATH = project_path("01_data", "db", "smr.db")


def load_draft(conn, draft_id):
    row = conn.execute(
        """
        SELECT
            draft_id,
            source_id,
            draft_type,
            entity_type,
            entity_id,
            title,
            summary,
            candidate_category,
            candidate_tags,
            governance_status,
            approval_status,
            source_path,
            source_rel_path,
            draft_payload_json
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
        "draft_type": row[2],
        "entity_type": row[3],
        "entity_id": row[4],
        "title": row[5],
        "summary": row[6],
        "candidate_category": row[7],
        "candidate_tags": row[8],
        "governance_status": row[9],
        "approval_status": row[10],
        "source_path": row[11],
        "source_rel_path": row[12],
        "draft_payload_json": row[13],
    }


def render_page(draft, knowledge_id, imported_at):
    payload = loads_json(draft["draft_payload_json"], {})
    candidate_tags = loads_json(draft["candidate_tags"], [])
    source_type = draft["draft_type"]
    page_type = page_type_for_category(draft["candidate_category"])

    lines = [
        "---",
        f"page_id: {knowledge_id}",
        f"page_type: {page_type}",
        f"entity_type: {draft['entity_type']}",
        f"entity_id: {draft['entity_id']}",
        f"title: {draft['title']}",
        "status: active",
        f"source_id: {draft['source_id']}",
        f"source_type: {source_type}",
        f"updated_at: {imported_at}",
        "---",
        "",
        f"# {draft['title']}",
        "",
        "## Latest Compiled Insight",
        "",
        draft["summary"],
        "",
        "## Governance Trace",
        "",
        f"- imported_from_draft: `{draft['draft_id']}`",
        f"- imported_at: `{imported_at}`",
        f"- approval_status: `{draft['approval_status']}`",
        "",
        "## Source Notes",
        "",
        f"- source_rel_path: `{draft['source_rel_path']}`",
        f"- candidate_category: `{draft['candidate_category']}`",
        f"- candidate_tags: `{', '.join(candidate_tags) if candidate_tags else ''}`",
        "",
        "## Payload Snapshot",
        "",
        "```json",
        dumps_json(payload),
        "```",
        "",
    ]
    return "\n".join(lines)


def import_wiki_draft(conn, draft_id, source="import_wiki_entry.py"):
    ensure_ingest_draft_table(conn)
    ensure_knowledge_index_table(conn)
    ensure_import_execution_table(conn)

    draft = load_draft(conn, draft_id)
    if draft["governance_status"] != "ready" or draft["approval_status"] not in {"approved", "auto_ready"}:
        raise SystemExit("Draft must be ready and approved/auto_ready before import")
    if imported_source_exists(conn, draft["source_id"]):
        raise SystemExit("This source has already been imported")

    knowledge_id = knowledge_id_for(
        draft["candidate_category"],
        draft["entity_id"],
        source_id=draft["source_id"],
    )
    target_path = wiki_abs_path_for(
        draft["candidate_category"],
        draft["entity_id"],
        source_id=draft["source_id"],
    )
    target_rel_path = wiki_rel_path_for(
        draft["candidate_category"],
        draft["entity_id"],
        source_id=draft["source_id"],
    )
    imported_at = now_ts()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(render_page(draft, knowledge_id, imported_at), encoding="utf-8")

    conn.execute(
        """
        INSERT INTO smr_wiki_knowledge_index (
            knowledge_id,
            page_type,
            entity_type,
            entity_id,
            title,
            page_path,
            page_rel_path,
            status,
            source_id,
            source_type,
            imported_at,
            updated_at,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(knowledge_id) DO UPDATE SET
            title=excluded.title,
            page_path=excluded.page_path,
            page_rel_path=excluded.page_rel_path,
            status=excluded.status,
            source_id=excluded.source_id,
            source_type=excluded.source_type,
            imported_at=excluded.imported_at,
            updated_at=excluded.updated_at,
            metadata_json=excluded.metadata_json
        """,
        (
            knowledge_id,
            page_type_for_category(draft["candidate_category"]),
            draft["entity_type"],
            draft["entity_id"],
            draft["title"],
            str(target_path),
            target_rel_path,
            "active",
            draft["source_id"],
            draft["draft_type"],
            imported_at,
            imported_at,
            draft["draft_payload_json"],
        ),
    )

    execution_id = generate_execution_id("wiki_import")
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            execution_id,
            draft["draft_id"],
            draft["source_id"],
            "import",
            "import",
            "imported",
            knowledge_id,
            target_rel_path,
            dumps_json({"candidate_category": draft["candidate_category"]}),
            imported_at,
        ),
    )

    conn.execute(
        """
        UPDATE smr_wiki_ingest_draft
        SET governance_status='blocked',
            review_reason_code='duplicate_source',
            review_reason='该 source 已经导入过正式 Wiki，不应重复导入。',
            updated_at=?
        WHERE draft_id=?
        """,
        (imported_at, draft["draft_id"]),
    )
    register_snapshot(
        conn,
        entity_type="wiki_draft",
        entity_id=draft["draft_id"],
        status="imported",
        source=source,
        relationships={
            "source_id": draft["source_id"],
            "knowledge_id": knowledge_id,
        },
        payload={
            "approval_status": draft["approval_status"],
            "candidate_category": draft["candidate_category"],
            "target_rel_path": target_rel_path,
            "import_execution_id": execution_id,
            "imported_at": imported_at,
        },
        created_at=imported_at,
    )
    register_snapshot(
        conn,
        entity_type="wiki_knowledge_entry",
        entity_id=knowledge_id,
        status="active",
        source=source,
        relationships={
            "draft_id": draft["draft_id"],
            "source_id": draft["source_id"],
            "entity_type": draft["entity_type"],
            "entity_id": draft["entity_id"],
        },
        payload={
            "title": draft["title"],
            "page_type": page_type_for_category(draft["candidate_category"]),
            "candidate_category": draft["candidate_category"],
            "target_rel_path": target_rel_path,
            "source_type": draft["draft_type"],
            "imported_at": imported_at,
        },
        created_at=imported_at,
    )
    return {
        "draft_id": draft["draft_id"],
        "knowledge_id": knowledge_id,
        "target_path": str(target_path),
        "target_rel_path": target_rel_path,
        "import_execution_id": execution_id,
        "imported_at": imported_at,
        "candidate_category": draft["candidate_category"],
    }


def main():
    parser = argparse.ArgumentParser(description="Import SMR Wiki entry from approved draft")
    parser.add_argument("--draft-id", required=True, help="Draft id to import")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    result = import_wiki_draft(conn, args.draft_id)
    conn.commit()
    conn.close()

    log_run(
        "import_wiki_entry.py",
        "success",
        "wiki entry imported",
        {
            "draft_id": result["draft_id"],
            "knowledge_id": result["knowledge_id"],
            "target_path": result["target_path"],
        },
    )
    print(f"Imported draft: {result['draft_id']}")
    print(f"Target: {result['target_path']}")


if __name__ == "__main__":
    main()
