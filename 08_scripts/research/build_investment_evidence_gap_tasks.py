#!/usr/bin/env python3
"""Build hard-evidence follow-up task snapshots for investment reports."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_investment_reports import evidence_gap_tasks_from_report
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "build_investment_evidence_gap_tasks.py"


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def action_id_from_entity(entity_id: str | None, payload: dict[str, Any] | None = None) -> str | None:
    payload = payload or {}
    if payload.get("action_id"):
        return payload.get("action_id")
    text = str(entity_id or "")
    if "__" in text:
        return text.split("__", 1)[1]
    return None


def date_from_entity(entity_id: str | None) -> str:
    text = str(entity_id or "")
    if "__" in text:
        prefix = text.split("__", 1)[0]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", prefix):
            return prefix
    return datetime.now().strftime("%Y-%m-%d")


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unknown"


def latest_report_entries(conn: sqlite3.Connection, action_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE entity_type='investment_report_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (max(limit * 5, limit),),
    ).fetchall()
    entries = []
    seen_actions: set[str] = set()
    for row in rows:
        payload = load_json(row["payload_json"], {})
        candidate_action_id = action_id_from_entity(row["entity_id"], payload)
        if not candidate_action_id:
            continue
        if action_id and candidate_action_id != action_id:
            continue
        if candidate_action_id in seen_actions:
            continue
        seen_actions.add(candidate_action_id)
        entries.append(
            {
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "status": row["status"],
                "source": row["source"],
                "relationships": load_json(row["relationships_json"], {}),
                "payload": payload,
                "snapshot_index": row["snapshot_index"],
                "created_at": row["created_at"],
                "action_id": candidate_action_id,
            }
        )
        if len(entries) >= limit:
            break
    return entries


def latest_action_map(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    row = conn.execute(
        """
        SELECT payload_json
        FROM task_registry_entry
        WHERE entity_type='portfolio_action_memo_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    payload = load_json(row["payload_json"], {}) if row else {}
    actions = payload.get("actions") or []
    return {action.get("action_id"): action for action in actions if action.get("action_id")}


def action_context(action_id: str, action: dict[str, Any] | None = None) -> dict[str, Any]:
    action = action or {}
    add = action.get("add") or {}
    remove = action.get("remove") or {}
    return {
        "action_id": action_id,
        "action_title": action.get("title") or action_id,
        "add_name": add.get("name") or add.get("ts_code") or "-",
        "add_code": add.get("ts_code") or "-",
        "remove_name": remove.get("name") or remove.get("ts_code") or "-",
        "remove_code": remove.get("ts_code") or "-",
    }


def md_cell(value: Any) -> str:
    text = "；".join(str(item) for item in value) if isinstance(value, list) else str(value or "-")
    return text.replace("\n", " ").replace("|", " / ").strip()


def render_tasks_markdown(entry: dict[str, Any], context: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    lines = [
        f"# 硬证据补证任务：{context.get('action_title') or entry['action_id']}",
        "",
        f"- action_id: `{entry['action_id']}`",
        f"- source_report_entry_id: `{entry['id']}`",
        f"- source_report_status: `{entry.get('status') or '-'}`",
        f"- generated_at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        "",
        "这些任务来自报告的关键变量审计。目标不是补一堆材料，而是验证本次调仓真正依赖的变量是否成立。",
        "",
    ]
    if not tasks:
        lines.extend(["## 当前结论", "", "未发现需要单独补证的关键变量。", ""])
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## 任务清单",
            "",
            "| 优先级 | 变量 | 研究问题 | 验收标准 | 对结论的影响 |",
            "|---|---|---|---|---|",
        ]
    )
    for task in tasks:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(task.get("priority")),
                    md_cell(task.get("variable_label")),
                    md_cell(task.get("research_question")),
                    md_cell(task.get("accepted_evidence")),
                    md_cell(task.get("thesis_effect")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## 优先来源与查询线索", ""])
    for index, task in enumerate(tasks, 1):
        lines.extend(
            [
                f"### {index}. {task.get('variable_label') or task.get('variable_id')}",
                "",
                f"- 优先来源：{md_cell(task.get('source_priority'))}",
                f"- 缺口原因：{md_cell(task.get('gap_reason'))}",
                "- 查询线索：",
            ]
        )
        query_templates = task.get("query_templates") or []
        if query_templates:
            lines.extend(f"  - `{item}`" for item in query_templates)
        else:
            lines.append("  - 暂无固定查询式，先从优先来源开始。")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_task_artifacts(entry: dict[str, Any], context: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, str]:
    action_id = entry["action_id"]
    batch_date = date_from_entity(entry.get("entity_id"))
    out_dir = project_path("02_research", "investment_evidence_gap_tasks", batch_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(action_id)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    payload = {
        "action_id": action_id,
        "source_report_entry_id": entry["id"],
        "source_report_entity_id": entry["entity_id"],
        "context": context,
        "tasks": tasks,
        "task_count": len(tasks),
        "priority_counts": dict(Counter(task.get("priority") or "P1" for task in tasks)),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_tasks_markdown(entry, context, tasks), encoding="utf-8")
    return {
        "task_json_rel_path": relative_to_project(json_path),
        "task_md_rel_path": relative_to_project(md_path),
    }


def build_for_entry(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    action_by_id: dict[str, dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    payload = entry.get("payload") or {}
    relationships = entry.get("relationships") or {}
    context = action_context(entry["action_id"], action_by_id.get(entry["action_id"]))
    tasks = evidence_gap_tasks_from_report(
        payload.get("dashboard_summary") or {},
        payload.get("source_discipline_audit") or {},
        context,
    )
    artifacts = {} if dry_run else write_task_artifacts(entry, context, tasks)
    result_payload = {
        "action_id": entry["action_id"],
        "action_context": context,
        "source_report_entry_id": entry["id"],
        "source_report_entity_id": entry["entity_id"],
        "source_report_status": entry["status"],
        "report_md_rel_path": payload.get("report_md_rel_path") or payload.get("model_response_text_rel_path"),
        "evidence_pack_md_rel_path": payload.get("evidence_pack_md_rel_path")
        or relationships.get("evidence_pack_md_rel_path"),
        "tasks": tasks,
        "task_count": len(tasks),
        "priority_counts": dict(Counter(task.get("priority") or "P1" for task in tasks)),
        "quality_boundary": "candidate research tasks; requires human review and source fetching before thesis upgrade",
        **artifacts,
    }
    if dry_run:
        return result_payload
    status = "open" if tasks else "pass"
    new_entry = register_snapshot(
        conn,
        entity_type="investment_evidence_gap_task_snapshot",
        entity_id=entry["entity_id"],
        status=status,
        source=SCRIPT_NAME,
        relationships={
            "source_report_entry_id": entry["id"],
            "report_md_rel_path": result_payload.get("report_md_rel_path"),
            "evidence_pack_md_rel_path": result_payload.get("evidence_pack_md_rel_path"),
            "task_md_rel_path": result_payload.get("task_md_rel_path"),
            "task_json_rel_path": result_payload.get("task_json_rel_path"),
        },
        payload=result_payload,
    )
    return {
        **result_payload,
        "new_entry_id": new_entry["id"],
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build investment hard-evidence gap task snapshots")
    parser.add_argument("--action-id")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    conn = connect_db()
    try:
        entries = latest_report_entries(conn, action_id=args.action_id, limit=max(args.limit, 1))
        if not entries:
            if args.allow_empty:
                print("[]")
                return
            raise SystemExit("No investment_report_snapshot entries found")
        action_by_id = latest_action_map(conn)
        results = [build_for_entry(conn, entry, action_by_id, dry_run=args.dry_run) for entry in entries]
        if not args.dry_run:
            conn.commit()
        log_run(
            SCRIPT_NAME,
            "success",
            "investment hard-evidence gap tasks built",
            {
                "action_id": args.action_id,
                "dry_run": args.dry_run,
                "result_count": len(results),
                "task_count": sum(result.get("task_count") or 0 for result in results),
                "results": [
                    {
                        "action_id": result.get("action_id"),
                        "task_count": result.get("task_count"),
                        "new_entry_id": result.get("new_entry_id"),
                    }
                    for result in results[:10]
                ],
            },
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
