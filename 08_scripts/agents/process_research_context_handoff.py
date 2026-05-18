#!/usr/bin/env python3
"""Process Hermes-like research context handoffs into workspace notes."""

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
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run

SUPPORTED_ENTITY_TYPES = {
    "dynamic_pool_snapshot",
    "portfolio_action_memo_snapshot",
    "research_quality_snapshot",
    "rotation_candidate_snapshot",
    "rotation_execution_plan_snapshot",
    "stock_objective_monitor_snapshot",
    "strategy_watch_batch",
    "trend_research_batch",
    "us_signal_snapshot",
}

TRANSCRIPT_FRESHNESS_LABELS = {
    "fresh": "很新",
    "usable": "还能参考",
    "stale": "偏旧",
    "missing": "缺失",
}

TRANSCRIPT_PROVIDER_LABELS = {
    "fool": "The Motley Fool",
}


def preview_list(values, limit=10):
    values = [str(value) for value in (values or []) if value not in (None, "")]
    if not values:
        return ""
    preview = values[:limit]
    suffix = " ..." if len(values) > limit else ""
    return ", ".join(preview) + suffix


def transcript_freshness_text(snapshot):
    snapshot = snapshot or {}
    freshness = str(snapshot.get("freshness_label") or "missing").strip().lower() or "missing"
    return TRANSCRIPT_FRESHNESS_LABELS.get(freshness, freshness or "缺失")


def transcript_snapshot_summary(snapshot):
    snapshot = snapshot or {}
    freshness_text = transcript_freshness_text(snapshot)
    summary = str(snapshot.get("summary") or "").strip()
    if summary:
        return f"{freshness_text} / {summary}"

    provider = TRANSCRIPT_PROVIDER_LABELS.get(str(snapshot.get("provider") or "").strip().lower(), snapshot.get("provider"))
    quarter_label = str(snapshot.get("quarter_label") or "").strip()
    published_at = str(snapshot.get("published_at") or "").strip()
    speaker_count = snapshot.get("speaker_count")
    speakers = [str(value).strip() for value in (snapshot.get("speakers") or []) if str(value).strip()]
    parts = []
    if provider:
        parts.append(str(provider))
    if quarter_label:
        parts.append(f"覆盖 {quarter_label} 业绩会")
    if published_at:
        parts.append(f"发布时间 {published_at[:10]}")
    if speaker_count not in (None, ""):
        parts.append(f"识别到约 {speaker_count} 位发言人")
    if speakers:
        parts.append(f"前几位包括 {', '.join(speakers[:3])}")
    if parts:
        return f"{freshness_text} / {' / '.join(parts)}"
    return f"{freshness_text} / 当前没有可直接复核的公开电话会文字稿。"


def transcript_followup_text(snapshot):
    snapshot = snapshot or {}
    freshness = str(snapshot.get("freshness_label") or "missing").strip().lower() or "missing"
    if freshness == "fresh":
        return "这份电话会稿比较新，可以直接拿来核对研究结论里对管理层口径的描述。"
    if freshness == "usable":
        return "这份电话会稿还能参考，但如果后面临近业绩或大事件窗口，仍要继续补更新原话。"
    if freshness == "stale":
        return "这份电话会稿已经偏旧，只能当背景资料，短线判断还要补更新公告、业绩材料或活动纪要。"
    return "当前没有公开电话会文字稿，不要把二手解读当管理层原话，先更多依赖公告、演示稿和投资者关系活动记录。"


def load_action_transcript_rows(conn, action):
    rows = []
    for role_label, stock in (
        ("调入腿", action.get("add") or {}),
        ("调出腿", action.get("remove") or {}),
        ("复核对象", action.get("subject") or {}),
    ):
        ts_code = stock.get("ts_code")
        if not ts_code:
            continue
        rows.append(
            {
                "role_label": role_label,
                "ts_code": ts_code,
                "name": stock.get("name") or ts_code,
                "snapshot": latest_public_transcript_snapshot(conn, ts_code) or {},
            }
        )
    return rows


def load_source_entry(conn, handoff):
    _, entry, _ = load_handoff_source_entry(
        conn,
        handoff,
        sync_active=True,
        updated_by="process_research_context_handoff.py",
        note="研究上下文 handoff 绑定到当前最新快照。",
    )
    if entry is None:
        raise SystemExit("Source registry entry not found for handoff")
    return entry


def render_dynamic_pool_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    counts = payload.get("counts") or {}
    active_codes = payload.get("active_codes_by_pool") or {}
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- snapshot_rel_path: `{relationships.get('snapshot_rel_path') or ''}`",
        f"- event_time: `{relationships.get('event_time') or ''}`",
        "",
        "## 池子概览",
        "",
        f"- structured_decisions: `{payload.get('structured_decisions', 0)}`",
        f"- live_code_count: `{payload.get('live_code_count', 0)}`",
        f"- watchlist_count: `{counts.get('watchlist', 0)}`",
        f"- candidate_count: `{counts.get('candidate', 0)}`",
        f"- recommended_count: `{counts.get('recommended', 0)}`",
        "",
        "## 当前关键池子",
        "",
        f"- recommended: `{preview_list(active_codes.get('recommended'))}`",
        f"- candidate: `{preview_list(active_codes.get('candidate'))}`",
        f"- watchlist: `{preview_list(active_codes.get('watchlist'))}`",
        "",
        "## 建议动作",
        "",
        "- 把今天最值得追踪的池子变化补一句解释。",
        "- 优先解释 recommended / candidate 的变化逻辑，不直接重写原始快照。",
        "- 如果池子变化反映 thesis 变化，再决定是否转成 wiki draft 或 decision 页面。",
        "",
    ]
    return "\n".join(lines)


def render_trend_batch_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- latest_us_date: `{relationships.get('latest_us_date') or ''}`",
        f"- latest_factor_date: `{relationships.get('latest_factor_date') or ''}`",
        f"- top_sector: `{relationships.get('top_sector') or ''}`",
        "",
        "## 批次概览",
        "",
        f"- target_count: `{payload.get('target_count', 0)}`",
        f"- target_ts_codes: `{preview_list(payload.get('target_ts_codes'))}`",
        f"- target_sectors: `{preview_list(payload.get('target_sectors'))}`",
        f"- summary_rel_path: `{payload.get('summary_rel_path') or ''}`",
        f"- industry_card_rel_path: `{payload.get('industry_card_rel_path') or ''}`",
        f"- stock_card_count: `{len(payload.get('stock_card_rel_paths') or [])}`",
        "",
        "## 建议动作",
        "",
        "- 抽出本批次最值得持续跟踪的 1-3 个主线。",
        "- 把行业卡和个股卡里的重复论点压缩成统一口径。",
        "- 高价值结论优先进入知识草稿，不直接把整批研究卡当正式知识。",
        "",
    ]
    return "\n".join(lines)


def render_quality_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- output_rel_path: `{relationships.get('output_rel_path') or payload.get('output_rel_path') or ''}`",
        "",
        "## 质量快照",
        "",
        f"- row_count: `{payload.get('row_count', 0)}`",
        f"- counts_by_pool: `{payload.get('counts_by_pool') or {}}`",
        f"- ts_codes: `{preview_list(payload.get('ts_codes'))}`",
        "",
        "## 建议动作",
        "",
        "- 优先标记研究空缺最多、但池子级别最高的标的。",
        "- 如果同一批标的长期重复缺口，把问题沉淀成 playbook 或 review checklist。",
        "- 不直接改研究卡原文，先给出治理和补强建议。",
        "",
    ]
    return "\n".join(lines)


def render_us_signal_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- signal_file_rel_path: `{relationships.get('signal_file_rel_path') or payload.get('signal_file_rel_path') or ''}`",
        "",
        "## 美股联动快照",
        "",
        f"- saved_count: `{payload.get('saved_count', 0)}`",
        f"- symbols: `{preview_list(payload.get('symbols'))}`",
        f"- signal_types: `{preview_list(payload.get('signal_types'))}`",
        f"- sectors: `{preview_list(payload.get('sectors'))}`",
        "",
        "## 建议动作",
        "",
        "- 只解释对 A/H 主线真正有影响的美股变化。",
        "- 如果只是噪音波动，不要强行沉淀成正式知识。",
        "- 如果影响持续存在，再把联动结论补进行业页或时间线。",
        "",
    ]
    return "\n".join(lines)


def render_objective_monitor_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    items = payload.get("items") or []
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- monitor_rel_path: `{relationships.get('monitor_rel_path') or payload.get('monitor_rel_path') or ''}`",
        "",
        "## 客观监控快照",
        "",
        f"- focus_strategy: `{payload.get('focus_strategy') or ''}`",
        f"- focus_count: `{payload.get('focus_count', 0)}`",
        f"- objective_view_counts: `{payload.get('objective_view_counts') or {}}`",
        "",
        "## 当前重点标的",
        "",
    ]
    if not items:
        lines.append("- 当前没有监控标的，先检查 portfolio_seed 或当前池是否为空。")
        lines.append("")
    else:
        for item in items[:10]:
            lines.extend(
                [
                    f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                    "",
                    f"- objective_view: `{item.get('objective_view') or '-'}`",
                    f"- latest_close / pct_chg: `{item.get('latest_close')}` / `{item.get('latest_pct_chg')}`",
                    f"- trend_strength / rsi_14: `{item.get('trend_strength')}` / `{item.get('rsi_14')}`",
                    f"- signal_tags: `{preview_list(item.get('signal_tags'))}`",
                ]
            )
            for watchpoint in item.get("watchpoints") or []:
                lines.append(f"- {watchpoint}")
            lines.append("")
    lines.extend(
        [
            "## 建议动作",
            "",
            "- 这条链只处理标的客观监控，不把仓位大小混进结论里。",
            "- 如果某只票的客观看法转弱，优先调整研究和跟踪优先级，再决定是否影响组合动作。",
            "- 需要组合层动作时，单独交给 `portfolio_pnl_snapshot / risk_monitor_snapshot`（组合盈亏/风控快照）处理。",
            "",
        ]
    )
    return "\n".join(lines)


def render_strategy_watch_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    top_focus_items = payload.get("top_focus_items") or []
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- summary_rel_path: `{relationships.get('summary_rel_path') or payload.get('summary_rel_path') or ''}`",
        f"- objective_monitor_rel_path: `{relationships.get('objective_monitor_rel_path') or ''}`",
        "",
        "## 策略观察批次",
        "",
        f"- focus_strategy: `{payload.get('focus_strategy') or ''}`",
        f"- item_count: `{payload.get('item_count', 0)}`",
        f"- priority_counts: `{payload.get('priority_counts') or {}}`",
        "",
        "## 当前优先盯盘标的",
        "",
    ]
    if not top_focus_items:
        lines.append("- 当前没有优先盯盘标的，请先检查策略观察卡批次是否为空。")
        lines.append("")
    else:
        for item in top_focus_items:
            priority = item.get("priority") or {}
            trend_state = item.get("trend_state") or {}
            valuation_pressure = item.get("valuation_pressure") or {}
            research_staleness = item.get("research_staleness") or {}
            public_transcript = item.get("public_transcript") or {}
            lines.extend(
                [
                    f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                    "",
                    f"- priority: `{priority.get('label', '-')}` / score=`{priority.get('score', '-')}`",
                    f"- objective_view: `{item.get('objective_view') or '-'}`",
                    f"- trend_state: `{trend_state.get('label', '-')}` / {trend_state.get('summary', '-')}",
                    f"- valuation_pressure: `{valuation_pressure.get('label', '-')}` / {valuation_pressure.get('summary', '-')}",
                    f"- research_staleness: `{research_staleness.get('label', '-')}` / {research_staleness.get('summary', '-')}",
                    f"- 管理层原话: {transcript_snapshot_summary(public_transcript)}",
                    f"- 原话使用建议: {transcript_followup_text(public_transcript)}",
                ]
            )
            for watchpoint in (item.get("watchpoints") or [])[:2]:
                lines.append(f"- 观察点：{watchpoint}")
            for check_item in (item.get("next_check_items") or [])[:2]:
                lines.append(f"- 下一检查项：{check_item}")
            lines.append("")
    lines.extend(
        [
            "## 建议动作",
            "",
            "- 优先把高优先级标的压缩成日报和调度板里的 1 到 3 个具体观察动作。",
            "- 研究过旧或缺失的票，优先补公告、季报和外部研究锚点，再决定是否升级观点。",
            "- 这批卡片仍然只回答“现在该盯什么”，不把真实仓位大小混进结论。",
            "",
        ]
    )
    return "\n".join(lines)


def render_rotation_candidate_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- summary_rel_path: `{relationships.get('summary_rel_path') or payload.get('summary_rel_path') or ''}`",
        "",
        "## 轮动候选概览",
        "",
        f"- holdings_reference_count: `{payload.get('holdings_reference_count', 0)}`",
        f"- opportunity_count: `{payload.get('opportunity_count', 0)}`",
        f"- rotation_pair_count: `{payload.get('rotation_pair_count', 0)}`",
        "",
        "## 优先调入候选",
        "",
    ]
    top_add_candidates = payload.get("top_add_candidates") or []
    if not top_add_candidates:
        lines.append("- 当前没有可优先调入的候选，请先检查 recommended / candidate 是否为空。")
        lines.append("")
    else:
        for item in top_add_candidates:
            public_transcript = item.get("public_transcript") or {}
            lines.extend(
                [
                    f"### {item.get('name') or item['ts_code']} / {item['ts_code']}",
                    "",
                    f"- primary_pool: `{item.get('primary_pool') or '-'}`",
                    f"- objective_view: `{item.get('objective_view') or '-'}`",
                    f"- rotation_in_score: `{item.get('rotation_in_score')}`",
                    f"- trend_state: `{(item.get('trend_state') or {}).get('label', '-')}` / {(item.get('trend_state') or {}).get('summary', '-')}",
                    f"- 管理层原话: {transcript_snapshot_summary(public_transcript)}",
                ]
            )
            for watchpoint in (item.get("watchpoints") or [])[:2]:
                lines.append(f"- 观察点：{watchpoint}")
            lines.append("")
    lines.extend(["## 优先轮动对", ""])
    rotation_pairs = payload.get("rotation_pairs") or []
    if not rotation_pairs:
        lines.append("- 当前还没有明确的轮动对，先继续观察机会池和持仓参照层。")
        lines.append("")
    else:
        for pair in rotation_pairs[:3]:
            add_item = pair.get("add") or {}
            remove_item = pair.get("remove") or {}
            add_transcript = add_item.get("public_transcript") or {}
            remove_transcript = remove_item.get("public_transcript") or {}
            lines.extend(
                [
                    f"### 调入 {add_item.get('name') or add_item.get('ts_code', '-')} / {add_item.get('ts_code') or '-'}",
                    "",
                    f"- 对应调出：`{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`",
                    f"- rotation_type: `{pair.get('fit_label') or '-'}`",
                    f"- pair_score: `{pair.get('pair_score')}`",
                    f"- 管理层原话对比：调入腿 {transcript_snapshot_summary(add_transcript)}；调出腿 {transcript_snapshot_summary(remove_transcript)}",
                ]
            )
            for reason in (pair.get("expected_positive_change") or [])[:2]:
                lines.append(f"- 预期正向变化：{reason}")
            for risk in (pair.get("risk_flags") or [])[:2]:
                lines.append(f"- 风险：{risk}")
            lines.append("")
    lines.extend(
        [
            "## 建议动作",
            "",
            "- 先把轮动候选当成“结构优化观察单”，不要直接把它当成自动交易指令。",
            "- 真正执行前，仍要叠加开仓门禁、风险集中度和真实仓位约束。",
            "- 如果同主线内出现更强机会，优先考虑做强换弱，而不是无边界加新票。",
            "",
        ]
    )
    return "\n".join(lines)


def render_rotation_execution_plan_note(handoff, entry):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    plans = payload.get("plans") or []
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- summary_rel_path: `{relationships.get('summary_rel_path') or payload.get('summary_rel_path') or ''}`",
        "",
        "## 执行方案概览",
        "",
        f"- plan_mode: `{payload.get('plan_mode') or ''}`",
        f"- holding_count: `{payload.get('holding_count', 0)}`",
        f"- slot_capital: `{payload.get('slot_capital')}`",
        f"- slot_pct: `{payload.get('slot_pct')}`",
        f"- total_exposure_pct: `{payload.get('total_exposure_pct')}`",
        f"- plan_count: `{payload.get('plan_count', 0)}`",
        f"- status_counts: `{payload.get('status_counts') or {}}`",
        "",
        "## 优先执行方案",
        "",
    ]
    if not plans:
        lines.append("- 当前没有可执行的方案草案，请先检查轮动候选是否为空。")
        lines.append("")
    else:
        for plan in plans[:3]:
            add_item = plan.get("add") or {}
            remove_item = plan.get("remove") or {}
            gate = plan.get("gate_result") or {}
            uplift = plan.get("uplift") or {}
            lines.extend(
                [
                    f"### 调入 {add_item.get('name') or add_item.get('ts_code', '-')} / {add_item.get('ts_code') or '-'}",
                    "",
                    f"- 对应调出：`{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`",
                    f"- gate_status: `{gate.get('status') or '-'}`",
                    f"- trade_amount: `{plan.get('trade_amount')}`",
                    f"- trade_amount_pct: `{plan.get('trade_amount_pct')}`",
                    f"- suggested_shares: `{plan.get('suggested_shares') or '-'}`",
                    f"- uplift_summary: {uplift.get('summary') or '-'}",
                ]
            )
            for item in (plan.get("execution_checklist") or [])[:2]:
                lines.append(f"- 执行检查：{item}")
            for risk in (plan.get("risk_flags") or [])[:2]:
                lines.append(f"- 风险：{risk}")
            lines.append("")
    lines.extend(
        [
            "## 建议动作",
            "",
            "- 先把这层当成执行前草案，不要直接当成自动交易指令。",
            "- 如果 `gate_status=ready`，下一步可以进入更细的止损、目标价和仓位比例设计。",
            "- 如果仍是 `reference_only`，等真实持仓主表补齐后，这层会自动切到真实仓位模式。",
            "",
        ]
    )
    return "\n".join(lines)


def render_portfolio_action_memo_note(handoff, entry, conn):
    payload = entry.get("payload", {})
    relationships = entry.get("relationships", {})
    actions = payload.get("actions") or []
    lines = [
        f"# 研究上下文草稿：{handoff['entity_type']} / {handoff['entity_id']}",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- source_entry_id: `{entry['id']}`",
        f"- summary_rel_path: `{relationships.get('summary_rel_path') or payload.get('summary_rel_path') or ''}`",
        "",
        "## 动作概览",
        "",
        f"- action_mode: `{payload.get('action_mode') or ''}`",
        f"- action_count: `{payload.get('action_count', 0)}`",
        f"- priority_counts: `{payload.get('priority_counts') or {}}`",
        f"- action_type_counts: `{payload.get('action_type_counts') or {}}`",
        "",
        "## 今日主张",
        "",
    ]
    for item in payload.get("primary_call") or ["当前没有明确主张。"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 优先动作", ""])
    if not actions:
        lines.append("- 当前没有可收敛的组合动作。")
        lines.append("")
    else:
        for action in actions[:4]:
            add_item = action.get("add") or {}
            remove_item = action.get("remove") or {}
            subject = action.get("subject") or {}
            transcript_rows = load_action_transcript_rows(conn, action)
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
                lines.append(f"- 调入腿：`{add_item.get('ts_code') or '-'} {add_item.get('name') or ''}`")
            if remove_item:
                lines.append(f"- 调出腿：`{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`")
            if subject:
                lines.append(f"- 对象：`{subject.get('ts_code') or '-'} {subject.get('name') or ''}`")
            for row in transcript_rows:
                lines.append(
                    f"- {row['role_label']}原话：{row['name']} / {row['ts_code']} / {transcript_snapshot_summary(row['snapshot'])}"
                )
                lines.append(f"- {row['role_label']}原话建议：{transcript_followup_text(row['snapshot'])}")
            for reason in (action.get("rationale") or [])[:2]:
                lines.append(f"- 支撑：{reason}")
            for check in (action.get("next_checks") or [])[:2]:
                lines.append(f"- 下一步：{check}")
            for risk in (action.get("risk_flags") or [])[:2]:
                lines.append(f"- 风险：{risk}")
            lines.append("")
    lines.extend(
        [
            "## 建议动作",
            "",
            "- 这层负责把已有快照收敛成“今天先做什么”的优先清单。",
            "- 如果仍是 `reference_only`，只把它当组合观察和计划草案，不当成真实下单指令。",
            "- 等真实持仓主表补齐后，这层可以继续升级成更正式的执行前决策单。",
            "",
        ]
    )
    return "\n".join(lines)


def render_note(handoff, entry, conn):
    entity_type = handoff["entity_type"]
    if entity_type == "dynamic_pool_snapshot":
        return render_dynamic_pool_note(handoff, entry)
    if entity_type == "portfolio_action_memo_snapshot":
        return render_portfolio_action_memo_note(handoff, entry, conn)
    if entity_type == "trend_research_batch":
        return render_trend_batch_note(handoff, entry)
    if entity_type == "research_quality_snapshot":
        return render_quality_note(handoff, entry)
    if entity_type == "rotation_candidate_snapshot":
        return render_rotation_candidate_note(handoff, entry)
    if entity_type == "rotation_execution_plan_snapshot":
        return render_rotation_execution_plan_note(handoff, entry)
    if entity_type == "stock_objective_monitor_snapshot":
        return render_objective_monitor_note(handoff, entry)
    if entity_type == "strategy_watch_batch":
        return render_strategy_watch_note(handoff, entry)
    if entity_type == "us_signal_snapshot":
        return render_us_signal_note(handoff, entry)
    raise SystemExit(f"Unsupported research context entity_type: {entity_type}")


def main():
    parser = argparse.ArgumentParser(description="Process Hermes-like research context handoff")
    parser.add_argument("--handoff-id", required=True)
    parser.add_argument("--complete", action="store_true", help="Complete handoff after note generation")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    handoff = get_handoff(args.handoff_id)
    if handoff["to_profile_id"] != "hermes_research_curator":
        raise SystemExit("This handoff does not belong to hermes_research_curator")
    if handoff["entity_type"] not in SUPPORTED_ENTITY_TYPES:
        raise SystemExit("This script only supports research context handoffs")

    profile = get_profile("hermes_research_curator")
    workspace = profile_workspace_path(profile)
    notes_dir = workspace / "notes"
    note_path = notes_dir / f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}.md"

    conn = sqlite3.connect(DB_PATH)
    entry = load_source_entry(conn, handoff)

    if args.dry_run:
        print(f"handoff_id: {handoff['handoff_id']}")
        print(f"handoff_status: {handoff['status']}")
        print(f"entity_type: {handoff['entity_type']}")
        print(f"entity_id: {handoff['entity_id']}")
        print(f"source_entry_id: {entry['id']}")
        print(f"note_rel_path: {relative_to_project(note_path)}")
        conn.close()
        return

    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path.write_text(render_note(handoff, entry, conn) + "\n", encoding="utf-8")

    note_id = f"{handoff['entity_type']}__{handoff['entity_id']}__{handoff['handoff_id']}"
    note_entry = register_snapshot(
        conn,
        entity_type="research_context_note",
        entity_id=note_id,
        status="created",
        source="process_research_context_handoff.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "source_entity_type": handoff["entity_type"],
            "source_entity_id": handoff["entity_id"],
        },
        payload={
            "note_rel_path": relative_to_project(note_path),
            "source_entry_id": entry["id"],
        },
    )
    downstream_handoff = ensure_auto_handoff(
        conn,
        note_entry,
        note="研究上下文草稿已生成，自动转交 Hermes-like reporting 代理并入调度候选。",
        created_by="process_research_context_handoff.py",
    )

    outputs = {
        "note_rel_path": relative_to_project(note_path),
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
        resolved_by="hermes_research_curator",
        summary="研究上下文 handoff 已生成解释草稿。",
        outputs=outputs,
        source="process_research_context_handoff.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "process_research_context_handoff.py",
        "success",
        "research context handoff processed",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "note_rel_path": outputs["note_rel_path"],
            "handoff_status": record["status"],
            "downstream_handoff_result": downstream_handoff["reason"],
            "downstream_handoff_id": outputs["downstream_handoff_id"],
        },
    )
    print(f"Processed research context handoff: {handoff['handoff_id']}")
    print(f"  handoff_status={record['status']}")
    print(f"  note_rel_path={outputs['note_rel_path']}")
    if downstream_handoff["handoff"]:
        print(
            f"  downstream_handoff={downstream_handoff['reason']}: "
            f"{downstream_handoff['handoff']['handoff_id']} -> {downstream_handoff['handoff']['to_profile_id']}"
        )
    else:
        print(f"  downstream_handoff={downstream_handoff['reason']}")


if __name__ == "__main__":
    main()
