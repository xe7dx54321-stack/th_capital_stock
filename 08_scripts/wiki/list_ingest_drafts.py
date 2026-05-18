#!/usr/bin/env python3
"""List SMR Wiki ingest drafts."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_wiki import ensure_ingest_draft_table, loads_json

DB_PATH = project_path("01_data", "db", "smr.db")


def main():
    parser = argparse.ArgumentParser(description="List SMR Wiki ingest drafts")
    parser.add_argument("--governance-status", help="Filter by governance status")
    parser.add_argument("--candidate-category", help="Filter by candidate category")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to show")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_ingest_draft_table(conn)

    filters = []
    params = []
    if args.governance_status:
        filters.append("governance_status = ?")
        params.append(args.governance_status)
    if args.candidate_category:
        filters.append("candidate_category = ?")
        params.append(args.candidate_category)

    query = """
        SELECT
            draft_id,
            source_id,
            draft_type,
            entity_id,
            candidate_category,
            governance_status,
            approval_status,
            candidate_tags,
            title
        FROM smr_wiki_ingest_draft
    """
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY datetime(updated_at) DESC, draft_id DESC LIMIT ?"
    params.append(args.limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    print("| draft_id | source_id | draft_type | entity_id | category | governance | approval | tags | title |")
    print("|----------|-----------|------------|-----------|----------|------------|----------|------|-------|")
    for row in rows:
        draft_id, source_id, draft_type, entity_id, category, governance_status, approval_status, candidate_tags, title = row
        tags = ",".join(loads_json(candidate_tags, []))
        print(
            f"| {draft_id} | {source_id} | {draft_type} | {entity_id} | {category} | "
            f"{governance_status} | {approval_status} | {tags} | {title} |"
        )


if __name__ == "__main__":
    main()
