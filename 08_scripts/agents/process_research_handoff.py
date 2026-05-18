#!/usr/bin/env python3
"""Process Hermes-like research handoffs against review queue and wiki drafts."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
WIKI_DIR = Path(__file__).resolve().parents[1] / "wiki"
for path in (LIB_DIR, WIKI_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from import_wiki_entry import import_wiki_draft
from resolve_review import resolve_review_decision
from smr_agents import DB_PATH, get_handoff, resolve_handoff
from smr_runlog import log_run


def load_pending_review_drafts(conn, limit, candidate_category=None):
    filters = [
        "governance_status='review_required'",
        "approval_status IN ('pending_manual_review', 'reopened')",
    ]
    params = []
    if candidate_category:
        filters.append("candidate_category=?")
        params.append(candidate_category)

    query = f"""
        SELECT draft_id, title, candidate_category, governance_status, approval_status
        FROM smr_wiki_ingest_draft
        WHERE {' AND '.join(filters)}
        ORDER BY datetime(updated_at) DESC, draft_id DESC
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [
        {
            "draft_id": row[0],
            "title": row[1],
            "candidate_category": row[2],
            "governance_status": row[3],
            "approval_status": row[4],
        }
        for row in rows
    ]


def count_pending_reviews(conn):
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM smr_wiki_ingest_draft
        WHERE governance_status='review_required'
          AND approval_status IN ('pending_manual_review', 'reopened')
        """
    ).fetchone()
    return row[0] or 0


def load_draft_state(conn, draft_id):
    row = conn.execute(
        """
        SELECT draft_id, governance_status, approval_status, review_reason_code, title
        FROM smr_wiki_ingest_draft
        WHERE draft_id=?
        """,
        (draft_id,),
    ).fetchone()
    if not row:
        raise SystemExit(f"Draft not found: {draft_id}")
    return {
        "draft_id": row[0],
        "governance_status": row[1],
        "approval_status": row[2],
        "review_reason_code": row[3],
        "title": row[4],
    }


def summarize_outputs(review_result, import_result, remaining_count):
    payload = {
        "remaining_pending_review_count": remaining_count,
    }
    if review_result:
        payload["review_result"] = review_result
    if import_result:
        payload["import_result"] = import_result
    return payload


def select_drafts(conn, handoff, args):
    selected = []
    if args.draft_id:
        seen = set()
        for draft_id in args.draft_id:
            if draft_id in seen:
                continue
            seen.add(draft_id)
            selected.append(load_draft_state(conn, draft_id))
        return selected

    if handoff["entity_type"] == "wiki_draft":
        return [load_draft_state(conn, handoff["entity_id"])]

    if args.batch_limit > 0:
        return load_pending_review_drafts(
            conn,
            limit=args.batch_limit,
            candidate_category=args.candidate_category,
        )

    return []


def process_single_draft(conn, draft_id, args):
    draft_conn = sqlite3.connect(DB_PATH)
    try:
        review_result = resolve_review_decision(
            draft_conn,
            draft_id=draft_id,
            decision=args.decision,
            reason_code=args.reason_code,
            reason=args.reason,
            source="process_research_handoff.py",
        )
        import_result = None
        if args.decision == "approved" and args.import_approved:
            import_result = import_wiki_draft(
                draft_conn,
                draft_id=draft_id,
                source="process_research_handoff.py",
            )
        draft_conn.commit()
        return {"ok": True, "review_result": review_result, "import_result": import_result}
    except BaseException as exc:
        draft_conn.rollback()
        return {"ok": False, "error": str(exc), "draft_id": draft_id}
    finally:
        draft_conn.close()


def main():
    parser = argparse.ArgumentParser(description="Process Hermes-like research handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--draft-id", action="append", help="Draft id to review; can be repeated")
    parser.add_argument("--batch-limit", type=int, default=0, help="When handoff points to review_queue, pick the latest N pending drafts")
    parser.add_argument("--candidate-category", help="Only used with --batch-limit to narrow draft category")
    parser.add_argument("--decision", choices=["approved", "rejected", "reopened"])
    parser.add_argument("--reason-code")
    parser.add_argument("--reason")
    parser.add_argument("--import-approved", action="store_true", help="Import after approval")
    parser.add_argument("--complete-if-clear", action="store_true", help="Complete handoff when queue is clear")
    parser.add_argument("--accept-only", action="store_true", help="Only accept the handoff without reviewing")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "hermes_research_curator":
        raise SystemExit("This handoff does not belong to hermes_research_curator")
    if handoff["entity_type"] not in {"review_queue", "wiki_draft"}:
        raise SystemExit("This script only supports review_queue / wiki_draft handoffs")
    if args.accept_only and args.decision:
        raise SystemExit("--accept-only and --decision cannot be used together")

    conn = sqlite3.connect(DB_PATH)
    before_remaining = count_pending_reviews(conn)
    selected_drafts = select_drafts(conn, handoff, args)
    if args.decision and not selected_drafts:
        conn.close()
        raise SystemExit("Review decisions require --draft-id, --batch-limit, or a wiki_draft handoff")

    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"handoff_status: {handoff['status']}")
        print(f"entity_type: {handoff['entity_type']}")
        print(f"remaining_pending_review_count_before: {before_remaining}")
        print(f"selected_draft_count: {len(selected_drafts)}")
        if selected_drafts:
            for draft_before in selected_drafts:
                print(
                    f"draft: {draft_before['draft_id']} | "
                    f"title={draft_before['title']} | "
                    f"governance_status={draft_before['governance_status']} | "
                    f"approval_status={draft_before['approval_status']}"
                )
            print(f"decision: {args.decision}")
            print(f"import_after_approval: {args.import_approved}")
        else:
            print("draft: <未指定>")
        conn.close()
        return

    processed_results = []
    failed_results = []
    for draft in selected_drafts:
        if not args.decision:
            break
        result = process_single_draft(conn, draft["draft_id"], args)
        if result["ok"]:
            processed_results.append(result)
        else:
            failed_results.append(result)

    remaining_count = count_pending_reviews(conn)
    outputs = {
        "remaining_pending_review_count": remaining_count,
        "processed_count": len(processed_results),
        "failed_count": len(failed_results),
        "processed_draft_ids": [
            item["review_result"]["draft_id"] for item in processed_results if item.get("review_result")
        ],
        "failed_items": failed_results[:10],
    }
    if len(processed_results) == 1:
        outputs = summarize_outputs(
            processed_results[0].get("review_result"),
            processed_results[0].get("import_result"),
            remaining_count,
        )
        outputs["processed_count"] = 1
        outputs["failed_count"] = len(failed_results)
        outputs["failed_items"] = failed_results[:10]

    if args.complete_if_clear and remaining_count == 0 and not failed_results:
        record = resolve_handoff(
            conn,
            handoff_id=handoff["handoff_id"],
            status="completed",
            resolved_by="hermes_research_curator",
            summary="研究治理 handoff 已清空待审核队列，流程完成。",
            outputs=outputs,
            source="process_research_handoff.py",
        )
    elif args.decision or args.accept_only:
        record = resolve_handoff(
            conn,
            handoff_id=handoff["handoff_id"],
            status="accepted",
            resolved_by="hermes_research_curator",
            summary="研究治理 handoff 已更新处理进度。" if args.decision else "研究治理 handoff 已领取。",
            outputs=outputs,
            source="process_research_handoff.py",
        )
    else:
        record = get_handoff(handoff["handoff_id"])

    conn.commit()
    conn.close()

    log_run(
        "process_research_handoff.py",
        "success",
        "research handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "decision": args.decision,
            "draft_count": len(selected_drafts),
            "processed_count": len(processed_results),
            "failed_count": len(failed_results),
            "remaining_pending_review_count": remaining_count,
            "handoff_status": record["status"],
        },
    )
    print(f"Processed research handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  remaining_pending_review_count={remaining_count}")
    print(f"  selected_draft_count={len(selected_drafts)}")
    print(f"  processed_count={len(processed_results)}")
    print(f"  failed_count={len(failed_results)}")
    for item in processed_results[:5]:
        review_result = item.get("review_result")
        import_result = item.get("import_result")
        if review_result:
            print(f"  review_draft_id={review_result['draft_id']}")
            print(f"    review_decision={review_result['decision']}")
            print(f"    review_governance_status={review_result['governance_status']}")
            print(f"    review_approval_status={review_result['approval_status']}")
        if import_result:
            print(f"    imported_knowledge_id={import_result['knowledge_id']}")
            print(f"    imported_target_rel_path={import_result['target_rel_path']}")
    for item in failed_results[:5]:
        print(f"  failed_draft_id={item['draft_id']}")
        print(f"    failed_reason={item['error']}")


if __name__ == "__main__":
    main()
