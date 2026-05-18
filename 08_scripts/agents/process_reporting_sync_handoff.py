#!/usr/bin/env python3
"""Process reporting sync handoffs into dispatch-ready candidate blocks."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    DB_PATH,
    get_handoff,
    get_profile,
    load_handoff_source_entry,
    profile_workspace_path,
    resolve_handoff,
)
from smr_paths import env_or_project_path, normalize_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SUPPORTED_ENTITY_TYPES = {
    "research_context_note",
    "risk_update_candidate",
}


def latest_reporting_surface_date(conn):
    row = conn.execute(
        """
        SELECT entity_id
        FROM task_registry_entity_latest
        WHERE entity_type='daily_reporting_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if row and row[0]:
        return row[0]
    return datetime.now().strftime("%Y-%m-%d")


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="process_reporting_sync_handoff.py",
        note="日报同步 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for reporting sync handoff")
    return entry


def read_rel_path_text(rel_path):
    if not rel_path:
        return ""
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_section_bullets(text, headings, limit=6):
    bullets = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            continue
        if current not in headings:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if stripped in {"- 建议动作：", "- 建议动作:"}:
                continue
            bullets.append(stripped)
        if len(bullets) >= limit:
            break
    return bullets


def extract_metadata_lines(text, limit=6):
    lines = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            lines.append(stripped)
        if len(lines) >= limit:
            break
    return lines


def render_research_sync_candidate(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    note_rel_path = payload.get("note_rel_path")
    note_text = read_rel_path_text(note_rel_path)
    meta_lines = extract_metadata_lines(note_text)
    summary_lines = extract_section_bullets(
        note_text,
        {
            "执行方案概览",
            "优先执行方案",
            "客观监控快照",
            "轮动候选概览",
            "优先调入候选",
            "优先轮动对",
            "策略观察批次",
            "当前优先盯盘标的",
            "池子概览",
            "当前关键池子",
            "批次概览",
            "质量快照",
            "美股联动快照",
            "建议动作",
        },
        limit=8,
    )
    lines = [
        f"# 调度同步候选：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- source_note_rel_path: `{note_rel_path or ''}`",
        f"- source_entity_type: `{relationships.get('source_entity_type') or ''}`",
        f"- source_entity_id: `{relationships.get('source_entity_id') or ''}`",
        "",
        "## 建议并入调度板",
        "",
        f"### 研究上下文同步（{relationships.get('source_entity_type') or handoff['entity_type']}）",
        "",
    ]
    if meta_lines:
        lines.extend(meta_lines)
    if summary_lines:
        lines.extend(summary_lines)
    if not meta_lines and not summary_lines:
        lines.append("- 当前未提取到有效摘要，请回看 source note 原文。")
    lines.extend(
        [
            "- 处理原则：优先补充解释，不直接覆盖旧结论。",
            "- 若该上下文会影响次日优先级，把它折叠到 P0 / P1 任务区。",
            "",
        ]
    )
    return "\n".join(lines)


def render_risk_sync_candidate(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    candidate_rel_path = payload.get("risk_candidate_rel_path")
    candidate_text = read_rel_path_text(candidate_rel_path)
    meta_lines = extract_metadata_lines(candidate_text)
    summary_lines = extract_section_bullets(candidate_text, {"建议补充块"}, limit=8)
    lines = [
        f"# 调度同步候选：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- risk_candidate_rel_path: `{candidate_rel_path or ''}`",
        f"- source_entity_type: `{relationships.get('source_entity_type') or ''}`",
        f"- source_entity_id: `{relationships.get('source_entity_id') or ''}`",
        "",
        "## 建议并入调度板",
        "",
        f"### 风险上下文同步（{relationships.get('source_entity_type') or handoff['entity_type']}）",
        "",
    ]
    if meta_lines:
        lines.extend(meta_lines)
    if summary_lines:
        lines.extend(summary_lines)
    if not meta_lines and not summary_lines:
        lines.append("- 当前未提取到有效摘要，请回看 risk candidate 原文。")
    lines.extend(
        [
            "- 处理原则：风险说明优先补到调度板，不直接替代交易动作。",
            "- 若当前是 clear 快照，只保留占位说明，不把它升级成伪风险任务。",
            "",
        ]
    )
    return "\n".join(lines)


def render_sync_candidate(handoff, entry):
    if handoff["entity_type"] == "research_context_note":
        return render_research_sync_candidate(handoff, entry)
    if handoff["entity_type"] == "risk_update_candidate":
        return render_risk_sync_candidate(handoff, entry)
    raise SystemExit(f"Unsupported reporting sync entity_type: {handoff['entity_type']}")


def main():
    parser = argparse.ArgumentParser(description="Process reporting sync handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--complete", action="store_true", help="Complete handoff after sync candidate generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "hermes_reporting_editor":
        raise SystemExit("This handoff does not belong to hermes_reporting_editor")
    if handoff["entity_type"] not in SUPPORTED_ENTITY_TYPES:
        raise SystemExit("This script only supports research_context_note / risk_update_candidate handoffs")

    profile = get_profile("hermes_reporting_editor")
    workspace = profile_workspace_path(profile)
    dispatch_dir = workspace / "dispatch_updates"
    candidate_path = dispatch_dir / f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}.md"

    conn = sqlite3.connect(DB_PATH)
    dispatch_date = latest_reporting_surface_date(conn)
    entry = load_source_entry(conn, handoff)

    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"handoff_status: {handoff['status']}")
        print(f"entity_type: {handoff['entity_type']}")
        print(f"entity_id: {handoff['entity_id']}")
        print(f"source_entry_id: {entry['id']}")
        print(f"dispatch_date: {dispatch_date}")
        print(f"sync_candidate_rel_path: {relative_to_project(candidate_path)}")
        conn.close()
        return

    dispatch_dir.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(render_sync_candidate(handoff, entry) + "\n", encoding="utf-8")

    candidate_id = f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}"
    sync_entry = register_snapshot(
        conn,
        entity_type="dispatch_sync_candidate",
        entity_id=candidate_id,
        status="created",
        source="process_reporting_sync_handoff.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "source_entity_type": handoff["entity_type"],
            "source_entity_id": handoff["entity_id"],
        },
        payload={
            "dispatch_date": dispatch_date,
            "dispatch_sync_rel_path": relative_to_project(candidate_path),
            "source_entry_id": entry["id"],
        },
    )

    outputs = {
        "dispatch_date": dispatch_date,
        "dispatch_sync_rel_path": relative_to_project(candidate_path),
        "source_entry_id": entry["id"],
    }
    record = resolve_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        status="completed" if args.complete else "accepted",
        resolved_by="hermes_reporting_editor",
        summary="reporting sync handoff 已生成调度同步候选块。",
        outputs=outputs,
        source="process_reporting_sync_handoff.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "process_reporting_sync_handoff.py",
        "success",
        "reporting sync handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "dispatch_date": dispatch_date,
            "dispatch_sync_rel_path": outputs["dispatch_sync_rel_path"],
            "handoff_status": record["status"],
            "registry_entry_id": sync_entry["id"],
        },
    )
    print(f"Processed reporting sync handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  dispatch_date={dispatch_date}")
    print(f"  dispatch_sync_rel_path={outputs['dispatch_sync_rel_path']}")


if __name__ == "__main__":
    main()
