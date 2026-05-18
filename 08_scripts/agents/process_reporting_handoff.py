#!/usr/bin/env python3
"""Process Hermes-like reporting handoffs into note outputs and draft refresh."""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
WIKI_DIR = Path(__file__).resolve().parents[1] / "wiki"
for path in (LIB_DIR, WIKI_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from create_ingest_draft import upsert_draft
from smr_agents import DB_PATH, get_handoff, get_profile, load_handoff_source_entry, profile_workspace_path, resolve_handoff
from smr_paths import relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import draft_registry_status, ensure_ingest_draft_table, imported_source_exists


TRANSCRIPT_FRESHNESS_LABELS = {
    "fresh": "很新",
    "usable": "还能参考",
    "stale": "偏旧",
    "missing": "缺失",
}

REPORTING_ENTITY_LABELS = {
    "daily_reporting_snapshot": "日报快照",
    "daily_report_candidate": "日报候选稿",
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


def load_source_row_by_rel_path(conn, rel_path):
    row = conn.execute(
        """
        SELECT
            source_id,
            source_type,
            entity_type,
            entity_id,
            title,
            source_path,
            source_rel_path,
            created_at,
            updated_at,
            upstream_refs,
            tags,
            metadata_json
        FROM source_manifest
        WHERE source_rel_path=?
        LIMIT 1
        """,
        (rel_path,),
    ).fetchone()
    if not row:
        return None
    return {
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


def transcript_freshness_label(snapshot):
    snapshot = snapshot or {}
    freshness = str(snapshot.get("freshness_label") or "missing").strip().lower() or "missing"
    return TRANSCRIPT_FRESHNESS_LABELS.get(freshness, freshness or "缺失")


def transcript_summary_line(snapshot):
    snapshot = snapshot or {}
    summary = str(snapshot.get("summary") or "").strip()
    if summary:
        return summary

    provider = str(snapshot.get("provider") or "").strip()
    quarter_label = str(snapshot.get("quarter_label") or "").strip()
    published_at = str(snapshot.get("published_at") or "").strip()
    speaker_count = snapshot.get("speaker_count")
    speakers = [str(value).strip() for value in (snapshot.get("speakers") or []) if str(value).strip()]
    parts = []
    if provider:
        parts.append(provider)
    if quarter_label:
        parts.append(f"覆盖 {quarter_label} 业绩会")
    if published_at:
        parts.append(f"发布时间 {published_at[:10]}")
    if speaker_count not in (None, ""):
        parts.append(f"识别到约 {speaker_count} 位发言人")
    if speakers:
        parts.append(f"前几位包括 {', '.join(speakers[:3])}")
    return " / ".join(parts) if parts else "当前没有可直接复核的公开电话会文字稿。"


def transcript_followup_line(snapshot):
    snapshot = snapshot or {}
    freshness = str(snapshot.get("freshness_label") or "missing").strip().lower() or "missing"
    if freshness == "fresh":
        return "这份原话比较新，可以直接拿来核对日报和调度板里对管理层口径的描述。"
    if freshness == "usable":
        return "这份原话还能参考，但如果后面临近业绩或事件窗口，仍要继续补更新版本。"
    if freshness == "stale":
        return "现有原话已经偏旧，只能当背景资料，短线结论还要补新公告、业绩稿或活动纪要。"
    return "当前没有公开电话会文字稿，不要把二手解读当管理层原话，先更多依赖公告、演示稿和投资者关系活动记录。"


def normalize_transcript_snapshot(snapshot):
    return snapshot or {}


def remember_transcript_item(index, item):
    ts_code = item.get("ts_code")
    if not ts_code:
        return
    snapshot = normalize_transcript_snapshot(item.get("public_transcript"))
    current = index.get(ts_code)
    if current and current.get("snapshot"):
        return
    index[ts_code] = {
        "name": item.get("name") or ts_code,
        "ts_code": ts_code,
        "snapshot": snapshot,
    }


def collect_transcript_index(strategy_watch_batch, rotation_candidate_snapshot):
    index = {}
    for item in (strategy_watch_batch.get("items") or []) + (strategy_watch_batch.get("top_focus_items") or []):
        remember_transcript_item(index, item)
    for item in (rotation_candidate_snapshot.get("top_add_candidates") or []) + (
        rotation_candidate_snapshot.get("top_reduce_candidates") or []
    ):
        remember_transcript_item(index, item)
    for pair in rotation_candidate_snapshot.get("rotation_pairs") or []:
        remember_transcript_item(index, pair.get("add") or {})
        remember_transcript_item(index, pair.get("remove") or {})
    return index


def action_transcript_effect(action, transcript_index):
    rows = []
    for role_label, stock in (
        ("调入腿", action.get("add") or {}),
        ("调出腿", action.get("remove") or {}),
        ("复核对象", action.get("subject") or {}),
    ):
        ts_code = stock.get("ts_code")
        if not ts_code:
            continue
        entry = transcript_index.get(ts_code) or {
            "name": stock.get("name") or ts_code,
            "ts_code": ts_code,
            "snapshot": {},
        }
        snapshot = entry.get("snapshot") or {}
        rows.append(
            (
                role_label,
                entry.get("name") or ts_code,
                ts_code,
                str(snapshot.get("freshness_label") or "missing").strip().lower() or "missing",
                transcript_summary_line(snapshot).rstrip("。.;；"),
            )
        )
    if not rows:
        return []

    freshness_set = {row[3] for row in rows}
    if freshness_set <= {"missing"}:
        tail = "这条动作目前主要靠趋势、公告和研究锚点支撑，不适合硬讲管理层最新表态变化。"
    elif "fresh" in freshness_set or "usable" in freshness_set:
        tail = "至少有一侧存在可用原话锚点，可以用来核对管理层口径是否支持这条动作。"
    else:
        tail = "现有原话都偏旧，只能当背景资料；若要强化这条动作，先补更新原话或会后材料。"

    line = "；".join(
        f"{role} {name} / {ts_code}：{transcript_freshness_label({'freshness_label': freshness})}，{summary}"
        for role, name, ts_code, freshness, summary in rows
    )
    return [f"- {action.get('title') or '-'}：{line}。{tail}"]


def render_management_quote_focus(strategy_watch_batch, rotation_candidate_snapshot, portfolio_action_memo_snapshot):
    watch_items = strategy_watch_batch.get("items") or strategy_watch_batch.get("top_focus_items") or []
    transcript_index = collect_transcript_index(strategy_watch_batch, rotation_candidate_snapshot)
    if not watch_items and not (portfolio_action_memo_snapshot.get("actions") or []):
        return []

    counts = {"fresh": 0, "usable": 0, "stale": 0, "missing": 0}
    for item in watch_items:
        freshness = str(((item.get("public_transcript") or {}).get("freshness_label")) or "missing").strip().lower() or "missing"
        if freshness not in counts:
            freshness = "missing"
        counts[freshness] += 1

    lines = [
        "## 管理层原话使用提醒",
        "",
        f"- 当前重点研究对象里，原话状态分布：很新 `{counts['fresh']}` / 还能参考 `{counts['usable']}` / 偏旧 `{counts['stale']}` / 缺失 `{counts['missing']}`",
        "- 这只是在回答“原话证据够不够硬”，不直接代表基本面好坏。",
    ]
    if counts["missing"] or counts["stale"]:
        lines.append("- 当前 A/H 跟踪池里很多票没有稳定公开电话会稿，所以原话缺失时，应更多依赖公告、演示稿和投资者关系活动记录。")
    lines.append("")

    gap_items = [
        item
        for item in watch_items
        if str(((item.get("public_transcript") or {}).get("freshness_label")) or "missing").strip().lower() in {"missing", "stale"}
    ]
    if gap_items:
        lines.extend(["### 当前最该补原话的标的", ""])
        for item in gap_items[:3]:
            snapshot = item.get("public_transcript") or {}
            lines.append(
                f"- {item.get('name') or item.get('ts_code') or '-'} / {item.get('ts_code') or '-'}："
                f"{transcript_freshness_label(snapshot)}，{transcript_followup_line(snapshot)}"
            )
        lines.append("")

    actions = portfolio_action_memo_snapshot.get("actions") or []
    if actions:
        lines.extend(["### 对今日动作的影响", ""])
        for action in actions[:4]:
            lines.extend(action_transcript_effect(action, transcript_index))
        lines.append("")
    return lines


def render_external_research_digest(digest):
    items = (digest or {}).get("items") or []
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
                f"- eps_yuan: `{item.get('eps_yuan') or {}}`",
                f"- pe_multiple: `{item.get('pe_multiple') or {}}`",
                f"- source_rel_path: `{item.get('source_rel_path') or '-'}`",
                "",
            ]
        )
    return lines


def render_high_value_reporting_digest(digest):
    items = (digest or {}).get("items") or []
    if not items:
        return []

    lines = [
        "## 高价值证据优先队列",
        "",
        f"- priority_rule: `{digest.get('priority_rule') or '-'}`",
        f"- focus_count: `{digest.get('focus_count', 0)}`",
        "",
    ]
    for item in items[:8]:
        lines.extend(
            [
                f"### {item.get('name') or item.get('ts_code') or '-'} / {item.get('ts_code') or '-'}",
                "",
                f"- source_family: `{item.get('source_family') or '-'}`",
                f"- priority_score: `{item.get('priority_score') or '-'}`",
                f"- headline: {item.get('headline') or item.get('summary') or '-'}",
                f"- latest_at: `{item.get('latest_at') or '-'}`",
                f"- source_rel_paths: `{item.get('source_rel_paths') or []}`",
                "",
            ]
        )
    return lines


def render_official_material_digest(digest):
    items = (digest or {}).get("items") or []
    if not items:
        return []

    lines = [
        "## 官方一手材料摘要",
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
                f"- freshness_label: `{item.get('freshness_label') or '-'}`",
                f"- item_count: `{item.get('item_count') or 0}`",
                f"- latest_event_type: `{item.get('latest_event_type') or '-'}`",
                f"- latest_publish_time: `{item.get('latest_publish_time') or '-'}`",
                f"- latest_title: {item.get('latest_title') or '-'}",
                f"- summary: {item.get('summary') or '-'}",
                f"- source_rel_paths: `{item.get('source_rel_paths') or []}`",
                "",
            ]
        )
    return lines


def render_public_transcript_digest(digest):
    items = (digest or {}).get("items") or []
    if not items:
        return []

    lines = [
        "## 公开电话会文字稿",
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
                f"- provider: `{item.get('provider') or '-'}`",
                f"- freshness_label: `{item.get('freshness_label') or '-'}`",
                f"- published_at: `{item.get('published_at') or '-'}`",
                f"- quarter_label: `{item.get('quarter_label') or '-'}`",
                f"- speaker_count: `{item.get('speaker_count') or 0}`",
                f"- speakers: `{item.get('speakers') or []}`",
                f"- summary: {item.get('summary') or '-'}",
                f"- source_rel_path: `{item.get('source_rel_path') or '-'}`",
                "",
            ]
        )
    return lines


def render_public_analyst_signal_digest(digest):
    items = (digest or {}).get("items") or []
    if not items:
        return []

    lines = [
        "## 公开卖方信号摘要",
        "",
        f"- focus_strategy: `{digest.get('focus_strategy') or '-'}`",
        f"- focus_count: `{digest.get('focus_count', 0)}`",
        "",
    ]
    for item in items:
        spread = item.get("spread_avg_target_pct")
        spread_text = "-" if spread is None else f"{'+' if spread > 0 else ''}{spread:.2f}%"
        lines.extend(
            [
                f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                "",
                f"- pool_types: `{','.join(item.get('pool_types') or []) or '-'}`",
                f"- provider: `{item.get('provider') or '-'}`",
                f"- mean_consensus: `{item.get('mean_consensus') or '-'}`",
                f"- analysts_count: `{item.get('analysts_count') or '-'}`",
                f"- average_target_raw: `{item.get('average_target_raw') or '-'}`",
                f"- spread_avg_target_pct: `{spread_text}`",
                f"- summary: {item.get('summary') or '-'}",
                f"- source_rel_path: `{item.get('source_rel_path') or '-'}`",
                "",
            ]
        )
    return lines


def render_objective_monitor_snapshot(snapshot):
    if not snapshot:
        return []
    lines = [
        "## 标的客观监控",
        "",
        f"- created_at: `{snapshot.get('created_at') or '-'}`",
        f"- monitor_rel_path: `{snapshot.get('monitor_rel_path') or '-'}`",
        f"- focus_strategy: `{snapshot.get('focus_strategy') or '-'}`",
        f"- focus_count: `{snapshot.get('focus_count', 0)}`",
        f"- objective_view_counts: `{snapshot.get('objective_view_counts') or {}}`",
        "",
    ]
    for item in (snapshot.get("items") or [])[:5]:
        lines.extend(
            [
                f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                "",
                f"- objective_view: `{item.get('objective_view') or '-'}`",
                f"- latest_close / pct_chg: `{item.get('latest_close')}` / `{item.get('latest_pct_chg')}`",
                f"- trend_strength / rsi_14: `{item.get('trend_strength')}` / `{item.get('rsi_14')}`",
                f"- signal_tags: `{','.join(item.get('signal_tags') or []) or '-'}`",
                "",
            ]
        )
    return lines


def render_strategy_watch_batch(batch):
    if not batch:
        return []
    lines = [
        "## 标的策略观察卡摘要",
        "",
        f"- created_at: `{batch.get('created_at') or '-'}`",
        f"- summary_rel_path: `{batch.get('summary_rel_path') or '-'}`",
        f"- objective_monitor_rel_path: `{batch.get('objective_monitor_rel_path') or '-'}`",
        f"- focus_strategy: `{batch.get('focus_strategy') or '-'}`",
        f"- item_count: `{batch.get('item_count', 0)}`",
        f"- priority_counts: `{batch.get('priority_counts') or {}}`",
        "",
    ]
    for item in (batch.get("top_focus_items") or [])[:3]:
        priority = item.get("priority") or {}
        trend_state = item.get("trend_state") or {}
        lines.extend(
            [
                f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                "",
                f"- priority: `{priority.get('label', '-')}` / score=`{priority.get('score', '-')}`",
                f"- objective_view: `{item.get('objective_view') or '-'}`",
                f"- trend_state: `{trend_state.get('label', '-')}` / {trend_state.get('summary', '-')}",
                f"- signal_tags: `{','.join(item.get('signal_tags') or []) or '-'}`",
            ]
        )
        for watchpoint in (item.get("watchpoints") or [])[:1]:
            lines.append(f"- 核心观察点：{watchpoint}")
        for check_item in (item.get("next_check_items") or [])[:1]:
            lines.append(f"- 下一检查项：{check_item}")
        lines.append("")
    return lines


def render_rotation_candidate_snapshot(snapshot):
    if not snapshot:
        return []
    lines = [
        "## 机会发现 / 轮动候选",
        "",
        f"- created_at: `{snapshot.get('created_at') or '-'}`",
        f"- summary_rel_path: `{snapshot.get('summary_rel_path') or '-'}`",
        f"- holdings_reference_count: `{snapshot.get('holdings_reference_count', 0)}`",
        f"- opportunity_count: `{snapshot.get('opportunity_count', 0)}`",
        f"- rotation_pair_count: `{snapshot.get('rotation_pair_count', 0)}`",
        "",
    ]
    for pair in (snapshot.get("rotation_pairs") or [])[:3]:
        add_item = pair.get("add") or {}
        remove_item = pair.get("remove") or {}
        lines.extend(
            [
                f"### 调入 {add_item.get('name') or add_item.get('ts_code', '-')} / {add_item.get('ts_code') or '-'}",
                "",
                f"- 对应调出: `{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`",
                f"- rotation_type: `{pair.get('fit_label') or '-'}`",
                f"- pair_score: `{pair.get('pair_score')}`",
            ]
        )
        for reason in (pair.get("expected_positive_change") or [])[:1]:
            lines.append(f"- 预期正向变化：{reason}")
        for risk in (pair.get("risk_flags") or [])[:1]:
            lines.append(f"- 主要风险：{risk}")
        lines.append("")
    return lines


def render_rotation_execution_plan_snapshot(snapshot):
    if not snapshot:
        return []
    lines = [
        "## 执行方案草案",
        "",
        f"- created_at: `{snapshot.get('created_at') or '-'}`",
        f"- summary_rel_path: `{snapshot.get('summary_rel_path') or '-'}`",
        f"- rotation_snapshot_rel_path: `{snapshot.get('rotation_snapshot_rel_path') or '-'}`",
        f"- plan_mode: `{snapshot.get('plan_mode') or '-'}`",
        f"- holding_count: `{snapshot.get('holding_count', 0)}`",
        f"- slot_capital: `{snapshot.get('slot_capital')}`",
        f"- total_exposure_pct: `{snapshot.get('total_exposure_pct')}`",
        f"- plan_count: `{snapshot.get('plan_count', 0)}`",
        f"- status_counts: `{snapshot.get('status_counts') or {}}`",
        "",
    ]
    for plan in (snapshot.get("plans") or [])[:3]:
        add_item = plan.get("add") or {}
        remove_item = plan.get("remove") or {}
        gate = plan.get("gate_result") or {}
        uplift = plan.get("uplift") or {}
        lines.extend(
            [
                f"### 调入 {add_item.get('name') or add_item.get('ts_code', '-')} / {add_item.get('ts_code') or '-'}",
                "",
                f"- 对应调出: `{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`",
                f"- gate_status: `{gate.get('status') or '-'}`",
                f"- trade_amount: `{plan.get('trade_amount')}`",
                f"- trade_amount_pct: `{plan.get('trade_amount_pct')}`",
                f"- uplift_summary: {uplift.get('summary') or '-'}",
            ]
        )
        for item in (plan.get("execution_checklist") or [])[:1]:
            lines.append(f"- 执行前检查：{item}")
        for risk in (plan.get("risk_flags") or [])[:1]:
            lines.append(f"- 主要风险：{risk}")
        lines.append("")
    return lines


def render_portfolio_action_memo_snapshot(snapshot):
    if not snapshot:
        return []
    lines = [
        "## 组合动作建议稿",
        "",
        f"- created_at: `{snapshot.get('created_at') or '-'}`",
        f"- summary_rel_path: `{snapshot.get('summary_rel_path') or '-'}`",
        f"- action_log_rel_path: `{snapshot.get('action_log_rel_path') or '-'}`",
        f"- action_mode: `{snapshot.get('action_mode') or '-'}`",
        f"- action_count: `{snapshot.get('action_count', 0)}`",
        f"- execution_precheck_status: `{snapshot.get('execution_precheck_status') or '-'}`",
        f"- priority_counts: `{snapshot.get('priority_counts') or {}}`",
        f"- action_type_counts: `{snapshot.get('action_type_counts') or {}}`",
        "",
    ]
    for line in (snapshot.get("primary_call") or [])[:3]:
        lines.append(f"- 主张：{line}")
    if snapshot.get("primary_call"):
        lines.append("")
    for action in (snapshot.get("actions") or [])[:4]:
        add_item = action.get("add") or {}
        remove_item = action.get("remove") or {}
        subject = action.get("subject") or {}
        lines.extend(
            [
                f"### {action.get('title') or '-'}",
                "",
                f"- action_type: `{action.get('action_type') or '-'}`",
                f"- priority: `{action.get('priority') or '-'}`",
                f"- summary: {action.get('summary') or '-'}",
            ]
        )
        if action.get("gate_status"):
            lines.append(f"- gate_status: `{action.get('gate_status')}`")
        if add_item:
            lines.append(f"- 调入腿: `{add_item.get('ts_code') or '-'} {add_item.get('name') or ''}`")
        if remove_item:
            lines.append(f"- 调出腿: `{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`")
        if subject:
            lines.append(f"- 对象: `{subject.get('ts_code') or '-'} {subject.get('name') or ''}`")
        for reason in (action.get("rationale") or [])[:1]:
            lines.append(f"- 支撑理由：{reason}")
        for item in (action.get("next_checks") or [])[:1]:
            lines.append(f"- 下一步检查：{item}")
        for risk in (action.get("risk_flags") or [])[:1]:
            lines.append(f"- 主要风险：{risk}")
        lines.append("")
    return lines


def render_reporting_note(
    handoff,
    report_rel_path,
    dispatch_rel_path,
    report_title,
    report_summary,
    external_research_digest,
    official_material_digest,
    public_transcript_digest,
    public_analyst_signal_digest,
    objective_monitor_snapshot,
    strategy_watch_batch,
    rotation_candidate_snapshot,
    rotation_execution_plan_snapshot,
    portfolio_action_memo_snapshot,
    high_value_reporting_digest,
):
    lines = [
        f"# 日报解释草稿：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- report_rel_path: `{report_rel_path or ''}`",
        f"- dispatch_board_rel_path: `{dispatch_rel_path or ''}`",
        "",
        "## 当前日报标题",
        "",
        report_title or "",
        "",
        "## 当前日报摘要",
        "",
        report_summary or "",
        "",
        "## 建议补充到调度板的说明",
        "",
        "- 明确今天最重要的 1-3 个跟踪动作。",
        "- 明确哪些结论应该沉淀成 daily_report / timeline 类知识草稿。",
        "- 若日报与调度板口径冲突，优先在调度板中补一句解释，不直接覆盖旧结论。",
        "",
    ]
    lines.extend(
        render_management_quote_focus(
            strategy_watch_batch,
            rotation_candidate_snapshot,
            portfolio_action_memo_snapshot,
        )
    )
    lines.extend(render_high_value_reporting_digest(high_value_reporting_digest))
    lines.extend(render_external_research_digest(external_research_digest))
    lines.extend(render_official_material_digest(official_material_digest))
    lines.extend(render_public_transcript_digest(public_transcript_digest))
    lines.extend(render_public_analyst_signal_digest(public_analyst_signal_digest))
    lines.extend(render_objective_monitor_snapshot(objective_monitor_snapshot))
    lines.extend(render_strategy_watch_batch(strategy_watch_batch))
    lines.extend(render_rotation_candidate_snapshot(rotation_candidate_snapshot))
    lines.extend(render_rotation_execution_plan_snapshot(rotation_execution_plan_snapshot))
    lines.extend(render_portfolio_action_memo_snapshot(portfolio_action_memo_snapshot))
    return "\n".join(lines)


def render_dispatch_candidate(
    handoff,
    report_rel_path,
    dispatch_rel_path,
    report_title,
    report_summary,
    draft_result,
    external_research_digest,
    official_material_digest,
    public_transcript_digest,
    public_analyst_signal_digest,
    objective_monitor_snapshot,
    strategy_watch_batch,
    rotation_candidate_snapshot,
    rotation_execution_plan_snapshot,
    portfolio_action_memo_snapshot,
    high_value_reporting_digest,
):
    lines = [
        f"# 调度板更新候选：{handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- report_rel_path: `{report_rel_path or ''}`",
        f"- dispatch_board_rel_path: `{dispatch_rel_path or ''}`",
        "",
        "## 建议追加块",
        "",
        f"### 日报 / 知识同步（{handoff['entity_id']}）",
        "",
        f"- 对应日报：`{report_rel_path or ''}`",
        f"- 日报标题：{report_title or ''}",
        f"- 日报摘要：{report_summary or ''}",
    ]
    if draft_result:
        lines.extend(
            [
                f"- 对应知识草稿：`{draft_result['draft_id']}`",
                f"- 草稿治理状态：`{draft_result['governance_status']}` / `{draft_result['approval_status']}`",
            ]
        )
    lines.extend(
        [
            "- 建议动作：",
            "  - 把今日最重要的 1-3 个观察动作补进调度面板。",
            "  - 把需要持续追踪的主题保留在时间线（timeline，时间线）或日报类知识草稿中。",
            "  - 不直接覆盖原结论，优先用“新增说明”方式补充。",
            "",
        ]
    )
    lines.extend(
        render_management_quote_focus(
            strategy_watch_batch,
            rotation_candidate_snapshot,
            portfolio_action_memo_snapshot,
        )
    )
    lines.extend(render_high_value_reporting_digest(high_value_reporting_digest))
    lines.extend(render_external_research_digest(external_research_digest))
    lines.extend(render_official_material_digest(official_material_digest))
    lines.extend(render_public_transcript_digest(public_transcript_digest))
    lines.extend(render_public_analyst_signal_digest(public_analyst_signal_digest))
    lines.extend(render_objective_monitor_snapshot(objective_monitor_snapshot))
    lines.extend(render_strategy_watch_batch(strategy_watch_batch))
    lines.extend(render_rotation_candidate_snapshot(rotation_candidate_snapshot))
    lines.extend(render_rotation_execution_plan_snapshot(rotation_execution_plan_snapshot))
    lines.extend(render_portfolio_action_memo_snapshot(portfolio_action_memo_snapshot))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Process Hermes-like reporting handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--refresh-draft", action="store_true", help="Refresh latest daily_report draft from source manifest")
    parser.add_argument("--complete", action="store_true", help="Complete handoff after note generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "hermes_reporting_editor":
        raise SystemExit("This handoff does not belong to hermes_reporting_editor")
    if handoff["entity_type"] not in {"daily_reporting_snapshot", "daily_report_candidate"}:
        raise SystemExit("This script only supports daily_reporting_snapshot / daily_report_candidate handoffs")

    profile = get_profile("hermes_reporting_editor")
    workspace = profile_workspace_path(profile)
    notes_dir = workspace / "notes"
    dispatch_dir = workspace / "dispatch_updates"
    note_path = notes_dir / f"{handoff['entity_id']}__{handoff['handoff_id']}.md"
    dispatch_candidate_path = dispatch_dir / f"{handoff['entity_id']}__{handoff['handoff_id']}.md"

    conn = sqlite3.connect(DB_PATH)
    dispatch_date = latest_reporting_surface_date(conn)
    handoff, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="process_reporting_handoff.py",
        note="日报 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for daily reporting handoff")
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    report_rel_path = relationships.get("latest_report_rel_path") or handoff.get("inputs", {}).get("relationships", {}).get("latest_report_rel_path")
    if not report_rel_path:
        report_rel_path = relationships.get("candidate_rel_path") or payload.get("candidate_rel_path")
    dispatch_rel_path = relationships.get("dispatch_board_rel_path") or handoff.get("inputs", {}).get("relationships", {}).get("dispatch_board_rel_path")
    report_title = payload.get("latest_report_title") or payload.get("candidate_title") or ""
    report_summary = payload.get("latest_report_summary") or payload.get("candidate_summary") or ""
    external_research_digest = payload.get("external_research_digest") or {}
    official_material_digest = payload.get("official_material_digest") or {}
    public_transcript_digest = payload.get("public_transcript_digest") or {}
    public_analyst_signal_digest = payload.get("public_analyst_signal_digest") or {}
    high_value_reporting_digest = payload.get("high_value_reporting_digest") or {}
    objective_monitor_snapshot = payload.get("objective_monitor_snapshot") or {}
    strategy_watch_batch = payload.get("strategy_watch_batch") or {}
    rotation_candidate_snapshot = payload.get("rotation_candidate_snapshot") or {}
    rotation_execution_plan_snapshot = payload.get("rotation_execution_plan_snapshot") or {}
    portfolio_action_memo_snapshot = payload.get("portfolio_action_memo_snapshot") or {}

    source_row = load_source_row_by_rel_path(conn, report_rel_path) if report_rel_path else None
    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"report_rel_path: {report_rel_path}")
        print(f"dispatch_rel_path: {dispatch_rel_path}")
        print(f"note_rel_path: {relative_to_project(note_path)}")
        print(f"dispatch_candidate_rel_path: {relative_to_project(dispatch_candidate_path)}")
        print(f"dispatch_date: {dispatch_date}")
        print(f"refresh_draft: {args.refresh_draft}")
        print(f"daily_report_source_found: {bool(source_row)}")
        conn.close()
        return

    notes_dir.mkdir(parents=True, exist_ok=True)
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        render_reporting_note(
            handoff,
            report_rel_path,
            dispatch_rel_path,
            report_title,
            report_summary,
            external_research_digest,
            official_material_digest,
            public_transcript_digest,
            public_analyst_signal_digest,
            objective_monitor_snapshot,
            strategy_watch_batch,
            rotation_candidate_snapshot,
            rotation_execution_plan_snapshot,
            portfolio_action_memo_snapshot,
            high_value_reporting_digest,
        )
        + "\n",
        encoding="utf-8",
    )

    draft_result = None
    if args.refresh_draft and source_row and not imported_source_exists(conn, source_row["source_id"]):
        ensure_ingest_draft_table(conn)
        draft_result = upsert_draft(conn, source_row)
        register_snapshot(
            conn,
            entity_type="wiki_draft",
            entity_id=draft_result["draft_id"],
            status=draft_registry_status(
                draft_result["governance_status"],
                draft_result["approval_status"],
                draft_result["review_reason_code"],
            ),
            source="process_reporting_handoff.py",
            relationships={
                "source_id": draft_result["source_id"],
                "draft_type": draft_result["draft_type"],
                "entity_type": draft_result["entity_type"],
                "entity_id": draft_result["entity_id"],
                "candidate_category": draft_result["candidate_category"],
            },
            payload={
                "approval_status": draft_result["approval_status"],
                "review_reason_code": draft_result["review_reason_code"],
                "review_reason": draft_result["review_reason"],
                "candidate_tags": draft_result["candidate_tags"],
                "source_rel_path": draft_result["source_rel_path"],
                "created_by_handoff": handoff["handoff_id"],
            },
            created_at=draft_result["updated_at"],
        )

    dispatch_candidate_path.write_text(
        render_dispatch_candidate(
            handoff,
            report_rel_path,
            dispatch_rel_path,
            report_title,
            report_summary,
            draft_result,
            external_research_digest,
            official_material_digest,
            public_transcript_digest,
            public_analyst_signal_digest,
            objective_monitor_snapshot,
            strategy_watch_batch,
            rotation_candidate_snapshot,
            rotation_execution_plan_snapshot,
            portfolio_action_memo_snapshot,
            high_value_reporting_digest,
        )
        + "\n",
        encoding="utf-8",
    )
    dispatch_candidate_id = f"{handoff['entity_id']}__{handoff['handoff_id']}"
    register_snapshot(
        conn,
        entity_type="dispatch_update_candidate",
        entity_id=dispatch_candidate_id,
        status="created",
        source="process_reporting_handoff.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "reporting_entity_type": handoff["entity_type"],
            "reporting_entity_id": handoff["entity_id"],
        },
        payload={
            "dispatch_date": dispatch_date,
            "dispatch_candidate_rel_path": relative_to_project(dispatch_candidate_path),
            "report_rel_path": report_rel_path,
            "dispatch_rel_path": dispatch_rel_path,
            "draft_id": draft_result["draft_id"] if draft_result else None,
        },
    )

    outputs = {
        "dispatch_date": dispatch_date,
        "note_rel_path": relative_to_project(note_path),
        "dispatch_candidate_rel_path": relative_to_project(dispatch_candidate_path),
        "report_rel_path": report_rel_path,
        "dispatch_rel_path": dispatch_rel_path,
    }
    if draft_result:
        outputs["draft_id"] = draft_result["draft_id"]
        outputs["draft_governance_status"] = draft_result["governance_status"]

    if args.complete:
        record = resolve_handoff(
            conn,
            handoff_id=handoff["handoff_id"],
            status="completed",
            resolved_by="hermes_reporting_editor",
            summary=(
                f"{REPORTING_ENTITY_LABELS.get(handoff['entity_type'], '日报')} handoff 已完成，"
                "已生成解释草稿并刷新相关知识草稿。"
            ),
            outputs=outputs,
            source="process_reporting_handoff.py",
        )
    else:
        record = resolve_handoff(
            conn,
            handoff_id=handoff["handoff_id"],
            status="accepted",
            resolved_by="hermes_reporting_editor",
            summary=(
                f"{REPORTING_ENTITY_LABELS.get(handoff['entity_type'], '日报')} handoff 已更新处理进度。"
                if handoff["status"] != "pending"
                else f"{REPORTING_ENTITY_LABELS.get(handoff['entity_type'], '日报')} handoff 已领取，已生成解释草稿。"
            ),
            outputs=outputs,
            source="process_reporting_handoff.py",
        )

    conn.commit()
    conn.close()

    log_run(
        "process_reporting_handoff.py",
        "success",
        "reporting handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "note_rel_path": outputs["note_rel_path"],
            "dispatch_candidate_rel_path": outputs["dispatch_candidate_rel_path"],
            "draft_id": outputs.get("draft_id"),
            "handoff_status": record["status"],
        },
    )
    print(f"Processed reporting handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  note_rel_path={outputs['note_rel_path']}")
    print(f"  dispatch_candidate_rel_path={outputs['dispatch_candidate_rel_path']}")
    if draft_result:
        print(f"  draft_id={draft_result['draft_id']}")
        print(f"  draft_governance_status={draft_result['governance_status']}")


if __name__ == "__main__":
    main()
