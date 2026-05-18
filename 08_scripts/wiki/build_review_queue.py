#!/usr/bin/env python3
"""Build a manual review queue from SMR Wiki ingest drafts."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path, relative_to_project
from smr_agents import ensure_auto_handoff
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import (
    dumps_json,
    ensure_ingest_draft_table,
    ensure_review_queue_execution_table,
    generate_execution_id,
    now_ts,
)

DB_PATH = project_path("01_data", "db", "smr.db")
EXPORT_DIR = project_path("11_smr_wiki", "drafts", "review_exports")


def load_queue_items(conn, include_rejected, include_blocked, limit):
    base_filter = [
        "(governance_status='review_required' AND approval_status IN ('pending_manual_review', 'reopened'))"
    ]
    if include_rejected:
        base_filter.append("approval_status='rejected'")
    if include_blocked:
        base_filter.append("(governance_status='blocked' AND approval_status!='rejected')")

    query = f"""
        SELECT
            draft_id,
            source_id,
            draft_type,
            entity_id,
            candidate_category,
            governance_status,
            approval_status,
            review_reason_code,
            review_reason,
            title
        FROM smr_wiki_ingest_draft
        WHERE {' OR '.join(base_filter)}
        ORDER BY datetime(updated_at) DESC, draft_id DESC
        LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()


def build_item(row):
    draft_id, source_id, draft_type, entity_id, category, governance_status, approval_status, reason_code, reason, title = row
    if approval_status == "rejected":
        queue = "reopen_review"
        available = ["reopened"]
    elif governance_status == "blocked":
        queue = "blocked_review"
        available = ["approved", "rejected"]
    else:
        queue = "manual_review"
        available = ["approved", "rejected"]

    return {
        "draft_id": draft_id,
        "source_id": source_id,
        "draft_type": draft_type,
        "entity_id": entity_id,
        "candidate_category": category,
        "governance_status": governance_status,
        "approval_status": approval_status,
        "review_reason_code": reason_code or "",
        "review_reason": reason or "",
        "queue": queue,
        "available_decisions": available,
        "title": title,
    }


def write_snapshot(items, execution_id):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = EXPORT_DIR / f"{execution_id}.md"
    lines = [
        "# SMR Wiki Review Queue",
        "",
        f"- execution_id: {execution_id}",
        f"- created_at: {now_ts()}",
        f"- item_count: {len(items)}",
        "",
        "| draft_id | queue | governance | approval | decisions | reason_code | title |",
        "|----------|-------|------------|----------|-----------|-------------|-------|",
    ]
    for item in items:
        decisions = ",".join(item["available_decisions"])
        title = item["title"].replace("|", "\\|")
        lines.append(
            f"| {item['draft_id']} | {item['queue']} | {item['governance_status']} | "
            f"{item['approval_status']} | {decisions} | {item['review_reason_code']} | {title} |"
        )
    export_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return export_path


def main():
    parser = argparse.ArgumentParser(description="Build SMR Wiki manual review queue")
    parser.add_argument("--include-rejected", action="store_true", help="Include rejected drafts for reopen queue")
    parser.add_argument("--include-blocked", action="store_true", help="Include blocked drafts")
    parser.add_argument("--limit", type=int, default=100, help="Maximum queue items")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_ingest_draft_table(conn)
    ensure_review_queue_execution_table(conn)

    items = [build_item(row) for row in load_queue_items(conn, args.include_rejected, args.include_blocked, args.limit)]
    execution_id = generate_execution_id("review_queue")
    export_path = write_snapshot(items, execution_id)

    counts = {}
    queue_counts = {}
    for item in items:
        key = f"{item['queue']}:{item['approval_status']}"
        counts[key] = counts.get(key, 0) + 1
        queue_counts[item["queue"]] = queue_counts.get(item["queue"], 0) + 1

    conn.execute(
        """
        INSERT INTO smr_wiki_review_queue_execution (
            execution_id,
            queue_mode,
            filters_json,
            item_count,
            counts_by_status_json,
            export_rel_path,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            execution_id,
            "manual_governance",
            dumps_json(
                {
                    "include_rejected": args.include_rejected,
                    "include_blocked": args.include_blocked,
                    "limit": args.limit,
                }
            ),
            len(items),
            dumps_json(counts),
            relative_to_project(export_path),
            now_ts(),
        ),
    )
    registry_entry = register_snapshot(
        conn,
        entity_type="review_queue",
        entity_id="manual_governance",
        status="queued" if items else "empty",
        source="build_review_queue.py",
        relationships={
            "execution_id": execution_id,
            "export_rel_path": relative_to_project(export_path),
        },
        payload={
            "item_count": len(items),
            "counts_by_status": counts,
            "counts_by_queue": queue_counts,
            "filters": {
                "include_rejected": args.include_rejected,
                "include_blocked": args.include_blocked,
                "limit": args.limit,
            },
            "draft_ids_sample": [item["draft_id"] for item in items[:10]],
        },
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="review queue 已刷新，自动转交 Hermes-like 研究治理代理处理。",
        created_by="build_review_queue.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "build_review_queue.py",
        "success",
        "review queue built",
        {
            "item_count": len(items),
            "execution_id": execution_id,
            "export_path": str(export_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Review queue items: {len(items)}")
    print(f"Snapshot: {export_path}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
