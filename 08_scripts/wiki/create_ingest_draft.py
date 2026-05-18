#!/usr/bin/env python3
"""Create minimal SMR Wiki ingest drafts from source_manifest entries."""

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
    cleanup_summary,
    draft_registry_status,
    dumps_json,
    ensure_ingest_draft_table,
    ensure_source_manifest_table,
    extract_first_paragraph,
    extract_section_text,
    loads_json,
    normalize_tags,
    now_ts,
    read_markdown,
)

DB_PATH = project_path("01_data", "db", "smr.db")

CATEGORY_BY_SOURCE = {
    "industry_research": "sectors",
    "stock_research": "stocks",
    "recommendation_card": "decisions",
    "daily_report": "timelines",
    "dispatch_snapshot": "timelines",
    "pool_snapshot": "timelines",
    "risk_alert_snapshot": "risk_cases",
    "external_source_snapshot": "timelines",
}

REVIEW_RULE_BY_SOURCE = {
    "industry_research": ("review_required", "pending_manual_review", "needs_human_judgement", "行业研究需要人工确认后再进入正式知识层。"),
    "stock_research": ("review_required", "pending_manual_review", "needs_human_judgement", "个股研究与 thesis 判断需要人工确认。"),
    "recommendation_card": ("review_required", "pending_manual_review", "needs_human_judgement", "推荐卡属于高判断密度对象，需要人工审核。"),
    "risk_alert_snapshot": ("review_required", "pending_manual_review", "needs_human_judgement", "风险相关结论默认进入人工审核。"),
    "daily_report": ("ready", "auto_ready", None, None),
    "dispatch_snapshot": ("ready", "auto_ready", None, None),
    "pool_snapshot": ("ready", "auto_ready", None, None),
    "external_source_snapshot": ("review_required", "pending_manual_review", "needs_human_judgement", "外部原始来源默认不自动转正式知识，需要人工判断。"),
}

SUMMARY_HEADINGS = {
    "industry_research": ["Conclusion", "Thesis", "结论"],
    "stock_research": ["Conclusion", "Thesis", "Suggested Pool"],
    "recommendation_card": ["Thesis", "Holding Period", "Current Portfolio Impact"],
    "daily_report": ["结构判断", "下一步关注", "趋势与因子结论"],
    "dispatch_snapshot": ["明日", "今日", "股票池当前状态"],
    "pool_snapshot": ["业务逻辑", "当前约定"],
    "risk_alert_snapshot": ["说明", "结论"],
    "external_source_snapshot": ["Extracted Text"],
}


def build_summary(source_type, source_path, title):
    text = read_markdown(source_path)
    if not text:
        return cleanup_summary(title)

    preferred_headings = SUMMARY_HEADINGS.get(source_type, [])
    section_summary = extract_section_text(text, preferred_headings)
    if section_summary:
        return section_summary

    first_paragraph = extract_first_paragraph(text)
    if first_paragraph:
        return first_paragraph

    return cleanup_summary(title)


def governance_for_source(source_type):
    return REVIEW_RULE_BY_SOURCE.get(source_type, ("review_required", "pending_manual_review", "needs_human_judgement", "默认需要人工审核。"))


def build_candidate_tags(source_row, metadata):
    upstream_refs = loads_json(source_row["upstream_refs"], [])
    raw_tags = loads_json(source_row["tags"], [])
    return normalize_tags(
        [
            source_row["source_type"],
            source_row["entity_type"],
            source_row["entity_id"],
            metadata.get("sector"),
            *upstream_refs[:3],
            *raw_tags[:4],
        ]
    )


def build_payload(source_row, category, metadata):
    return {
        "source_type": source_row["source_type"],
        "source_rel_path": source_row["source_rel_path"],
        "wiki_target_dir": f"11_smr_wiki/wiki/{category}",
        "entity_type": source_row["entity_type"],
        "entity_id": source_row["entity_id"],
        "metadata": metadata,
        "upstream_refs": loads_json(source_row["upstream_refs"], []),
    }


def batch_entity_id(args):
    if args.source_id:
        return f"source_id__{args.source_id}"
    if args.source_type:
        return f"source_type__{args.source_type}"
    return "all_active"


def load_sources(conn, args):
    filters = ["s.status='active'"]
    params = []

    if args.source_id:
        filters.append("s.source_id = ?")
        params.append(args.source_id)
    if args.source_type:
        filters.append("s.source_type = ?")
        params.append(args.source_type)
    elif not args.include_raw_external:
        filters.append("s.source_type != 'external_source_snapshot'")
    if not args.include_existing:
        filters.append("d.source_id IS NULL")

    query = f"""
        SELECT
            s.source_id,
            s.source_type,
            s.entity_type,
            s.entity_id,
            s.title,
            s.source_path,
            s.source_rel_path,
            s.created_at,
            s.updated_at,
            s.upstream_refs,
            s.tags,
            s.metadata_json
        FROM source_manifest s
        LEFT JOIN smr_wiki_ingest_draft d ON d.source_id = s.source_id
        WHERE {' AND '.join(filters)}
        ORDER BY datetime(COALESCE(s.updated_at, s.created_at)) DESC, s.source_id DESC
    """

    if args.limit:
        query += " LIMIT ?"
        params.append(args.limit)

    return [
        {
            "source_id": row[0],
            "source_type": row[1],
            "entity_type": row[2],
            "entity_id": row[3],
            "title": row[4],
            "source_path": row[5],
            "source_rel_path": row[6],
            "created_at": row[7],
            "updated_at": row[8],
            "upstream_refs": row[9],
            "tags": row[10],
            "metadata_json": row[11],
        }
        for row in conn.execute(query, params).fetchall()
    ]


def upsert_draft(conn, source_row):
    source_type = source_row["source_type"]
    metadata = loads_json(source_row["metadata_json"], {})
    category = CATEGORY_BY_SOURCE.get(source_type, "timelines")
    governance_status, approval_status, review_reason_code, review_reason = governance_for_source(source_type)
    draft_id = f"draft__{source_row['source_id']}"
    timestamp = now_ts()
    summary = build_summary(source_type, source_row["source_path"], source_row["title"])
    candidate_tags = build_candidate_tags(source_row, metadata)
    payload = build_payload(source_row, category, metadata)

    conn.execute(
        """
        INSERT INTO smr_wiki_ingest_draft (
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
            source_path,
            source_rel_path,
            draft_payload_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(draft_id) DO UPDATE SET
            draft_type=excluded.draft_type,
            entity_type=excluded.entity_type,
            entity_id=excluded.entity_id,
            title=excluded.title,
            summary=excluded.summary,
            candidate_category=excluded.candidate_category,
            candidate_tags=excluded.candidate_tags,
            governance_status=excluded.governance_status,
            approval_status=excluded.approval_status,
            review_reason_code=excluded.review_reason_code,
            review_reason=excluded.review_reason,
            source_path=excluded.source_path,
            source_rel_path=excluded.source_rel_path,
            draft_payload_json=excluded.draft_payload_json,
            updated_at=excluded.updated_at
        """,
        (
            draft_id,
            source_row["source_id"],
            source_type,
            source_row["entity_type"],
            source_row["entity_id"],
            source_row["title"],
            summary,
            category,
            dumps_json(candidate_tags),
            governance_status,
            approval_status,
            review_reason_code,
            review_reason,
            source_row["source_path"],
            source_row["source_rel_path"],
            dumps_json(payload),
            timestamp,
            timestamp,
        ),
    )
    return {
        "draft_id": draft_id,
        "source_id": source_row["source_id"],
        "draft_type": source_type,
        "entity_type": source_row["entity_type"],
        "entity_id": source_row["entity_id"],
        "candidate_category": category,
        "candidate_tags": candidate_tags,
        "governance_status": governance_status,
        "approval_status": approval_status,
        "review_reason_code": review_reason_code,
        "review_reason": review_reason,
        "source_rel_path": source_row["source_rel_path"],
        "updated_at": timestamp,
    }


def main():
    parser = argparse.ArgumentParser(description="Create SMR Wiki ingest drafts from source manifest entries")
    parser.add_argument("--source-id", help="Only create draft for a single source_id")
    parser.add_argument("--source-type", help="Only create drafts for one source type")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of sources to process")
    parser.add_argument("--include-existing", action="store_true", help="Rebuild drafts even if one already exists")
    parser.add_argument("--include-raw-external", action="store_true", help="Include external raw source snapshots")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_source_manifest_table(conn)
    ensure_ingest_draft_table(conn)

    sources = load_sources(conn, args)
    created = 0
    counts_by_status = {}
    draft_ids = []
    for source_row in sources:
        draft_snapshot = upsert_draft(conn, source_row)
        draft_ids.append(draft_snapshot["draft_id"])
        governance_status = draft_snapshot["governance_status"]
        counts_by_status[governance_status] = counts_by_status.get(governance_status, 0) + 1
        created += 1
        register_snapshot(
            conn,
            entity_type="wiki_draft",
            entity_id=draft_snapshot["draft_id"],
            status=draft_registry_status(
                draft_snapshot["governance_status"],
                draft_snapshot["approval_status"],
                draft_snapshot["review_reason_code"],
            ),
            source="create_ingest_draft.py",
            relationships={
                "source_id": draft_snapshot["source_id"],
                "draft_type": draft_snapshot["draft_type"],
                "entity_type": draft_snapshot["entity_type"],
                "entity_id": draft_snapshot["entity_id"],
                "candidate_category": draft_snapshot["candidate_category"],
            },
            payload={
                "approval_status": draft_snapshot["approval_status"],
                "review_reason_code": draft_snapshot["review_reason_code"],
                "review_reason": draft_snapshot["review_reason"],
                "candidate_tags": draft_snapshot["candidate_tags"],
                "source_rel_path": draft_snapshot["source_rel_path"],
            },
            created_at=draft_snapshot["updated_at"],
        )

    register_snapshot(
        conn,
        entity_type="ingest_draft_batch",
        entity_id=batch_entity_id(args),
        status="upserted" if created else "empty",
        source="create_ingest_draft.py",
        relationships={
            "source_id_filter": args.source_id,
            "source_type_filter": args.source_type,
            "include_existing": args.include_existing,
        },
        payload={
            "draft_count": created,
            "counts_by_status": counts_by_status,
            "draft_ids_sample": draft_ids[:10],
            "limit": args.limit,
        },
    )

    conn.commit()
    conn.close()

    log_run(
        "create_ingest_draft.py",
        "success",
        "ingest drafts created",
        {"draft_count": created, "counts_by_status": counts_by_status},
    )
    print(f"Ingest drafts upserted: {created}")
    for status, count in sorted(counts_by_status.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
