#!/usr/bin/env python3
"""Build a review queue/detail snapshot for human review operations."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_human_review_workflow import get_review_detail, list_review_queue
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_review_queue_snapshot.py"


def build_payload(conn: sqlite3.Connection, recommendation_id: str | None = None) -> dict:
    if recommendation_id:
        detail = get_review_detail(conn, recommendation_id)
        return {
            "generated_at": now_ts(),
            "mode": "review_detail",
            "summary": {
                "pending_human_review": 1 if detail.get("status") == "pending_human_review" else 0,
                "reduced_size_pending": 1 if detail.get("promotion_mode") == "reduced_size_pending" else 0,
            },
            "items": [detail] if detail.get("found") else [],
            "detail": detail,
        }
    items = list_review_queue(conn)
    return {
        "generated_at": now_ts(),
        "mode": "review_queue",
        "summary": {
            "pending_human_review": len(items),
            "reduced_size_pending": sum(1 for item in items if item.get("promotion_mode") == "reduced_size_pending"),
            "auto_approval_allowed": sum(1 for item in items if item.get("auto_approval_allowed")),
            "paper_order_allowed_before_approval": sum(1 for item in items if item.get("paper_order_allowed")),
        },
        "items": items,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Review Queue Snapshot",
        "",
        "## Pending Review",
        "| Ticker | Status | Thesis | Mode | Position | Warnings | Paper Order Allowed |",
        "|---|---|---|---|---:|---|---|",
    ]
    for item in payload.get("items") or []:
        warnings = ", ".join((item.get("supporting_warnings") or []) + (item.get("optional_warnings") or [])) or "-"
        lines.append(
            f"| {item.get('ticker')} | {item.get('status')} | {item.get('primary_thesis_type')} | "
            f"{item.get('promotion_mode') or '-'} | {item.get('suggested_position_pct') or 0} | "
            f"{warnings} | {item.get('paper_order_allowed')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build human review queue/detail snapshot")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--recommendation-id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.recommendation_id)
        register_snapshot(
            conn,
            entity_type="review_queue_snapshot",
            entity_id=args.recommendation_id or "latest",
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "review queue snapshot built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
