#!/usr/bin/env python3
"""Build Phase 32 priority evidence review packet."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase32_download_repair_workbench import build_payload as build_download_repair_payload
from smr_agents import DB_PATH
from smr_evidence_review_workbench import build_workbench, filter_workbench_items, recommended_first_pass_items
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _packet_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "workbench_item_id": item.get("workbench_item_id"),
        "evidence_id": item.get("evidence_id"),
        "repair_task_id": item.get("repair_task_id"),
        "priority": item.get("priority"),
        "ticker": item.get("ticker"),
        "company_name": item.get("company_name"),
        "item_type": item.get("item_type"),
        "variable_type": item.get("variable_type"),
        "sensitive_variable": item.get("sensitive_variable"),
        "quality_score": item.get("quality_score"),
        "quality_bucket": item.get("quality_bucket"),
        "lifecycle_status": item.get("lifecycle_status"),
        "review_status": item.get("review_status"),
        "quoted_span_preview": item.get("quoted_span_preview"),
        "source_url": item.get("source_url"),
        "source_type": item.get("source_type"),
        "linked_variable_pack": item.get("linked_variable_pack"),
        "link_status": item.get("link_status"),
        "limitations": item.get("limitations") or [],
        "recommended_action": item.get("recommended_action"),
        "allowed_actions": item.get("allowed_actions") or [],
        "blocked_actions": item.get("blocked_actions") or [],
        "action_command_dry_run": item.get("action_command_dry_run"),
    }


def build_payload(
    conn: sqlite3.Connection,
    *,
    tickers: str | None = None,
    ticker: str | None = None,
    priority: str | None = None,
    sensitive_only: bool = False,
) -> dict[str, Any]:
    workbench = build_workbench(conn, tickers=tickers, ticker=ticker)
    items = filter_workbench_items(workbench.get("items") or [], priority=priority, sensitive_only=sensitive_only)
    first_pass = recommended_first_pass_items(workbench.get("items") or [])
    repair = build_download_repair_payload(conn, tickers=tickers or ticker)
    summary = dict(workbench.get("summary") or {})
    summary["recommended_first_pass_items"] = len(first_pass)
    summary["packet_items"] = len(items)
    summary["download_repair_tasks"] = (repair.get("summary") or {}).get("repair_tasks", summary.get("download_repair_tasks", 0))
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "filters": {"priority": priority, "sensitive_only": sensitive_only, "ticker": ticker, "tickers": tickers},
        "items": [_packet_item(item) for item in items],
        "download_repair_tasks": repair.get("tasks") or [],
        "safety": workbench.get("safety") or {},
    }


def _quality_label(item: dict[str, Any]) -> str:
    score = item.get("quality_score")
    bucket = item.get("quality_bucket")
    return f"{score} / {bucket}" if score is not None or bucket else ""


def _render_item(index: int, item: dict[str, Any]) -> list[str]:
    title = f"{item.get('ticker') or 'UNKNOWN'} / {item.get('variable_type') or item.get('item_type')}"
    lines = [
        f"### {index}. {title}",
        f"- Evidence ID: {item.get('evidence_id') or item.get('repair_task_id')}",
        f"- Quality: {_quality_label(item)}",
        f"- Lifecycle: {item.get('lifecycle_status')} / {item.get('review_status')}",
        f"- Source: {item.get('source_url') or 'MISSING_SOURCE_URL'}",
        f"- Source type: {item.get('source_type')}",
        f"- Linked variable pack: {item.get('linked_variable_pack') or ''} ({item.get('link_status')})",
        f"- Sensitive variable: {item.get('sensitive_variable')}",
        f"- Quoted span: {item.get('quoted_span_preview') or ''}",
        f"- Limitations: {', '.join(item.get('limitations') or [])}",
        f"- Recommended action: {item.get('recommended_action')}",
        f"- Allowed actions: {', '.join(item.get('allowed_actions') or [])}",
        f"- Blocked actions: {', '.join(item.get('blocked_actions') or [])}",
        f"- Dry-run command: `{item.get('action_command_dry_run') or 'N/A'}`",
        "",
    ]
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    items = payload.get("items") or []
    high_items = [item for item in items if item.get("priority") == "high"]
    sensitive_items = [item for item in items if item.get("sensitive_variable")]
    review_required = [item for item in items if item.get("review_status") == "review_required"]
    lines = [
        "# Phase 32 Priority Evidence Review Packet",
        "",
        "## Summary",
        f"- Total workbench items: {summary.get('total_workbench_items')}",
        f"- High priority: {summary.get('high_priority')}",
        f"- Sensitive variable items: {summary.get('sensitive_variable_items')}",
        f"- Review required: {summary.get('review_required')}",
        f"- Download repair tasks: {summary.get('download_repair_tasks')}",
        f"- Recommended first pass: {summary.get('recommended_first_pass_items')}",
        "",
        "## Safety",
        "- Default commands are dry-run only.",
        "- Execute commands are not shown by default.",
        "- Evidence review does not allow promotion, pending creation, paper orders, or confirmed sensitive-variable upgrades.",
        "",
        "## High Priority Items",
    ]
    for index, item in enumerate(high_items or items[:10], start=1):
        lines.extend(_render_item(index, item))
    lines.append("## Sensitive Variable Items")
    for index, item in enumerate(sensitive_items[:20], start=1):
        lines.extend(_render_item(index, item))
    lines.append("## Review Required Items")
    for index, item in enumerate(review_required, start=1):
        lines.extend(_render_item(index, item))
    lines.append("## Download Repair Tasks")
    for index, task in enumerate(payload.get("download_repair_tasks") or [], start=1):
        lines.extend(
            [
                f"### {index}. {task.get('ticker')} / {task.get('recommended_action')}",
                f"- Repair task ID: {task.get('repair_task_id')}",
                f"- Source ID: {task.get('source_id')}",
                f"- Source: {task.get('source_url')}",
                f"- Reason: {task.get('reason')}",
                f"- Notes: {task.get('notes')}",
                "- Dry-run command: `python 08_scripts/jobs/upsert_download_unavailable_repair_tasks.py --dry-run --json`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 32 priority evidence review packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--ticker")
    parser.add_argument("--priority")
    parser.add_argument("--sensitive-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, ticker=args.ticker, priority=args.priority, sensitive_only=args.sensitive_only)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
