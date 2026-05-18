#!/usr/bin/env python3
"""Process Hermes-like risk handoffs into notes and update candidates."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    DB_PATH,
    ensure_auto_handoff,
    get_handoff,
    get_profile,
    load_handoff_source_entry,
    profile_workspace_path,
    resolve_handoff,
)
from smr_paths import relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SUPPORTED_ENTITY_TYPES = {
    "portfolio_pnl_snapshot",
    "risk_monitor_snapshot",
}


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="process_risk_handoff.py",
        note="风控 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for handoff")
    return entry


def render_external_research_digest(payload):
    digest = payload.get("external_research_digest") or {}
    items = digest.get("items") or []
    if not items:
        return []

    lines = [
        "## 外部研究锚点",
        "",
        f"- focus_strategy: `{digest.get('focus_strategy') or '-'}`",
        f"- focus_count: `{digest.get('focus_count', 0)}`",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                "",
                f"- pool_types: `{','.join(item.get('pool_types') or []) or '-'}`",
                f"- source_kind: `{item.get('source_kind') or '-'}`",
                f"- published_at: `{item.get('published_at') or '-'}`",
                f"- org_name: `{item.get('org_name') or '-'}`",
                f"- rating_name: `{item.get('rating_name') or '-'}`",
                f"- target_price_yuan: `{item.get('target_price_yuan') if item.get('target_price_yuan') is not None else '-'}`",
                f"- eps_yuan: `{item.get('eps_yuan') or {}}`",
                f"- pe_multiple: `{item.get('pe_multiple') or {}}`",
                f"- source_rel_path: `{item.get('source_rel_path') or '-'}`",
                "",
            ]
        )
    return lines


def render_reference_observations(payload):
    rows = payload.get("reference_observations") or []
    if not rows:
        return []
    lines = ["## 参考组合观察", ""]
    for item in rows:
        lines.append(f"- {item}")
    lines.append("")
    return lines


def render_risk_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    alert_count = payload.get("alert_count", 0)
    lines = [
        f"# 风险解释草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- source_status: `{entry['status']}`",
        "",
    ]

    if handoff["entity_type"] == "risk_monitor_snapshot":
        lines.extend(
            [
                "## 风险快照",
                "",
                f"- alert_count: `{alert_count}`",
                f"- counts_by_severity: `{payload.get('counts_by_severity') or {}}`",
                f"- counts_by_type: `{payload.get('counts_by_type') or {}}`",
                f"- open_position_count: `{payload.get('open_position_count', 0)}`",
                f"- unacknowledged_alert_count: `{payload.get('unacknowledged_alert_count', 0)}`",
                f"- alert_file_rel_path: `{relationships.get('alert_file_rel_path') or payload.get('alert_file_rel_path') or ''}`",
                "",
                "## 建议动作",
                "",
            ]
        )
        if alert_count > 0:
            lines.extend(
                [
                    "- 先看 critical，再看 warning，不要平均分配注意力。",
                    "- 未确认预警优先进入调度面板或次日跟踪清单。",
                    "- 同类预警重复出现时，优先沉淀成 risk case 或 playbook。",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "- 当前是 clear 快照，本次只保留一条占位解释，不新增风险动作。",
                    "- 如果后续连续多天都是 clear，可以把这类空快照改成更轻量的心跳记录。",
                    "- 不要为了“有输出”而强行制造风险结论。",
                    "",
                ]
            )
        lines.extend(render_reference_observations(payload))
        lines.extend(render_external_research_digest(payload))
    else:
        lines.extend(
            [
                "## 组合 PnL 快照",
                "",
                f"- open_position_count: `{payload.get('open_position_count', 0)}`",
                f"- updated_positions: `{payload.get('updated_positions', 0)}`",
                f"- profitable_positions: `{payload.get('profitable_positions', 0)}`",
                f"- losing_positions: `{payload.get('losing_positions', 0)}`",
                f"- total_pnl: `{payload.get('total_pnl', 0)}`",
                "",
                "## 建议动作",
                "",
                "- 亏损票变多时，优先检查是否和已有风险预警互相印证。",
                "- 如果总 PnL 转弱但预警没有同步抬头，说明风控口径可能还要补。",
                "- 只生成解释和候选动作，不直接改仓位。",
                "",
            ]
        )
    return "\n".join(lines)


def render_risk_candidate(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    alert_count = payload.get("alert_count", 0)
    lines = [
        f"# 风险治理候选：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        "",
        "## 建议补充块",
        "",
    ]

    if handoff["entity_type"] == "risk_monitor_snapshot":
        lines.extend(
            [
                f"- alert_count: `{alert_count}`",
                f"- counts_by_severity: `{payload.get('counts_by_severity') or {}}`",
                f"- counts_by_type: `{payload.get('counts_by_type') or {}}`",
                f"- alert_file_rel_path: `{relationships.get('alert_file_rel_path') or payload.get('alert_file_rel_path') or ''}`",
                "- 建议动作：",
            ]
        )
        if alert_count > 0:
            lines.extend(
                [
                    "  - 优先处理未确认 critical 预警。",
                    "  - 把重复出现的风险模式沉淀成 risk case。",
                    "  - 如果只是一次性噪音，不要扩大为长期规则。",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "  - 当前无新增预警，不追加风险动作。",
                    "  - 保留这条候选仅用于说明“今天风险面清空”。",
                    "  - 后续只有在重新出现真实预警时再升级为治理动作。",
                    "",
                ]
            )
        observations = payload.get("reference_observations") or []
        if observations:
            lines.append("- 参考组合观察：")
            for item in observations:
                lines.append(f"  - {item}")
            lines.append("")
        lines.extend(render_external_research_digest(payload))
    else:
        lines.extend(
            [
                f"- total_pnl: `{payload.get('total_pnl', 0)}`",
                f"- losing_positions: `{payload.get('losing_positions', 0)}` / `{payload.get('open_position_count', 0)}`",
                "- 建议动作：",
                "  - 检查亏损是否集中在同一主题或同一类 thesis。",
                "  - 把需要复盘的仓位写成次日任务，不直接替代交易动作。",
                "  - 如果亏损结构持续恶化，再补风险 playbook。",
                "",
            ]
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Process Hermes-like risk handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--complete", action="store_true", help="Complete handoff after note generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "hermes_risk_curator":
        raise SystemExit("This handoff does not belong to hermes_risk_curator")
    if handoff["entity_type"] not in SUPPORTED_ENTITY_TYPES:
        raise SystemExit("This script only supports risk_monitor_snapshot / portfolio_pnl_snapshot handoffs")

    profile = get_profile("hermes_risk_curator")
    workspace = profile_workspace_path(profile)
    notes_dir = workspace / "notes"
    updates_dir = workspace / "risk_updates"
    stem = f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}"
    note_path = notes_dir / f"{stem}.md"
    candidate_path = updates_dir / f"{stem}.md"

    conn = sqlite3.connect(DB_PATH)
    entry = load_source_entry(conn, handoff)

    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"handoff_status: {handoff['status']}")
        print(f"entity_type: {handoff['entity_type']}")
        print(f"entity_id: {handoff['entity_id']}")
        print(f"source_entry_id: {entry['id']}")
        print(f"note_rel_path: {relative_to_project(note_path)}")
        print(f"risk_candidate_rel_path: {relative_to_project(candidate_path)}")
        conn.close()
        return

    notes_dir.mkdir(parents=True, exist_ok=True)
    updates_dir.mkdir(parents=True, exist_ok=True)
    note_path.write_text(render_risk_note(handoff, entry) + "\n", encoding="utf-8")
    candidate_path.write_text(render_risk_candidate(handoff, entry) + "\n", encoding="utf-8")

    candidate_id = stem
    candidate_entry = register_snapshot(
        conn,
        entity_type="risk_update_candidate",
        entity_id=candidate_id,
        status="created",
        source="process_risk_handoff.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "source_entity_type": handoff["entity_type"],
            "source_entity_id": handoff["entity_id"],
        },
        payload={
            "note_rel_path": relative_to_project(note_path),
            "risk_candidate_rel_path": relative_to_project(candidate_path),
            "source_entry_id": entry["id"],
        },
    )
    downstream_handoff = ensure_auto_handoff(
        conn,
        candidate_entry,
        note="风险治理候选已生成，自动转交 Hermes-like reporting 代理并入调度候选。",
        created_by="process_risk_handoff.py",
    )

    outputs = {
        "note_rel_path": relative_to_project(note_path),
        "risk_candidate_rel_path": relative_to_project(candidate_path),
        "source_entry_id": entry["id"],
        "source_entity_type": handoff["entity_type"],
        "source_entity_id": handoff["entity_id"],
        "downstream_handoff_id": downstream_handoff["handoff"]["handoff_id"] if downstream_handoff["handoff"] else None,
        "downstream_handoff_result": downstream_handoff["reason"],
    }
    record = resolve_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        status="completed" if args.complete else "accepted",
        resolved_by="hermes_risk_curator",
        summary="风险 handoff 已生成解释草稿和治理候选块。",
        outputs=outputs,
        source="process_risk_handoff.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "process_risk_handoff.py",
        "success",
        "risk handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "note_rel_path": outputs["note_rel_path"],
            "risk_candidate_rel_path": outputs["risk_candidate_rel_path"],
            "handoff_status": record["status"],
            "downstream_handoff_result": downstream_handoff["reason"],
            "downstream_handoff_id": outputs["downstream_handoff_id"],
        },
    )
    print(f"Processed risk handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  note_rel_path={outputs['note_rel_path']}")
    print(f"  risk_candidate_rel_path={outputs['risk_candidate_rel_path']}")
    if downstream_handoff["handoff"]:
        print(
            f"  downstream_handoff={downstream_handoff['reason']}: "
            f"{downstream_handoff['handoff']['handoff_id']} -> {downstream_handoff['handoff']['to_profile_id']}"
        )
    else:
        print(f"  downstream_handoff={downstream_handoff['reason']}")


if __name__ == "__main__":
    main()
