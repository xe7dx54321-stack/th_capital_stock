#!/usr/bin/env python3
"""Export ingest drafts to Markdown files for manual review."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_runlog import log_run
from smr_wiki import ensure_ingest_draft_table, loads_json

DB_PATH = project_path("01_data", "db", "smr.db")
EXPORT_DIR = project_path("11_smr_wiki", "drafts", "ingest")


def load_drafts(conn, draft_id, limit):
    params = []
    query = """
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
            review_reason_code,
            review_reason,
            source_rel_path,
            draft_payload_json,
            created_at,
            updated_at
        FROM smr_wiki_ingest_draft
    """
    if draft_id:
        query += " WHERE draft_id = ?"
        params.append(draft_id)
    query += " ORDER BY datetime(updated_at) DESC, draft_id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(query, params).fetchall()


def render_draft_markdown(row):
    (
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
        review_reason_code,
        review_reason,
        source_rel_path,
        draft_payload_json,
        created_at,
        updated_at,
    ) = row

    payload = loads_json(draft_payload_json, {})
    tags = loads_json(candidate_tags, [])
    lines = [
        "---",
        f"draft_id: {draft_id}",
        f"source_id: {source_id}",
        f"draft_type: {draft_type}",
        f"entity_type: {entity_type}",
        f"entity_id: {entity_id}",
        f"candidate_category: {candidate_category}",
        f"governance_status: {governance_status}",
        f"approval_status: {approval_status}",
        f"created_at: {created_at}",
        f"updated_at: {updated_at}",
        "---",
        "",
        f"# {title}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Source",
        "",
        f"- source_rel_path: `{source_rel_path}`",
        f"- wiki_target_dir: `{payload.get('wiki_target_dir', '')}`",
        "",
        "## Candidate Tags",
        "",
        "- " + ", ".join(tags) if tags else "- no tags",
        "",
        "## Review Notes",
        "",
        f"- review_reason_code: `{review_reason_code or ''}`",
        f"- review_reason: {review_reason or 'none'}",
        "",
        "## Payload",
        "",
        "```json",
        draft_payload_json,
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export SMR Wiki ingest drafts to Markdown")
    parser.add_argument("--draft-id", help="Export a single draft")
    parser.add_argument("--limit", type=int, default=10, help="Maximum drafts to export")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_ingest_draft_table(conn)
    rows = load_drafts(conn, args.draft_id, args.limit)
    conn.close()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for row in rows:
        draft_id = row[0]
        export_path = EXPORT_DIR / f"{draft_id}.md"
        export_path.write_text(render_draft_markdown(row), encoding="utf-8")
        print(f"Exported: {export_path}")

    log_run(
        "export_draft_markdown.py",
        "success",
        "draft markdown exported",
        {"draft_count": len(rows), "export_dir": str(EXPORT_DIR)},
    )


if __name__ == "__main__":
    main()
