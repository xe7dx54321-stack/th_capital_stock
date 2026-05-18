#!/usr/bin/env python3
"""Build a portfolio action memo from current monitoring, strategy, and rotation layers."""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, ensure_auto_handoff, get_latest_registry_entry, get_registry_entry_by_id
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from build_execution_precheck import build_execution_precheck_for_date

OUTPUT_DIR = env_or_project_path("SMR_PORTFOLIO_ACTION_DIR", "04_portfolio", "actions")
LOG_DIR = env_or_project_path("SMR_PORTFOLIO_ACTION_LOG_DIR", "04_portfolio", "logs")

ACTION_TYPE_LABELS = {
    "swap_ready": "优先换仓",
    "swap_watch": "观察换仓",
    "swap_blocked": "门禁阻塞",
    "holding_watch": "持仓复核",
    "opportunity_followup": "机会跟踪",
}

PRIORITY_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

DISPLAY_LABELS = {
    "reference_only": "参照层建议",
    "real_positions": "真实持仓模式",
    "high": "高",
    "medium": "中",
    "low": "低",
    "ready": "可推进",
    "watch_only": "仅观察",
    "blocked": "阻塞",
    "unknown": "未知",
    "swap_ready": "优先换仓",
    "swap_watch": "观察换仓",
    "swap_blocked": "门禁阻塞",
    "holding_watch": "持仓复核",
    "opportunity_followup": "机会跟踪",
    "recommended": "推荐池",
    "candidate": "候选池",
    "watchlist": "观察池",
    "portfolio_seed": "持仓参照层",
    "none": "未分层",
    "trend_follow": "趋势跟随",
    "trend_positive": "趋势偏正",
    "observe": "观察",
    "repair_needed": "等待修复",
}


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ordered_unique(values):
    seen = set()
    results = []
    for value in values:
        if value in (None, ""):
            continue
        if value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def display_label(value):
    if value in (None, ""):
        return "-"
    return DISPLAY_LABELS.get(str(value), str(value))


def format_count_map(values):
    if not values:
        return "-"
    parts = []
    for key, count in values.items():
        parts.append(f"{display_label(key)}={count}")
    return " / ".join(parts)


def load_snapshot_entry(conn, entity_type, entity_id=None, required=True):
    if entity_id:
        entry = get_latest_registry_entry(conn, entity_type, entity_id)
        if entry is not None:
            return entry
    row = conn.execute(
        """
        SELECT id
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    if not row:
        if required:
            raise SystemExit(f"{entity_type} not found")
        return None
    entry = get_registry_entry_by_id(conn, row[0])
    if entry is None and required:
        raise SystemExit(f"latest {entity_type} entry missing")
    return entry


def action_title(add_item=None, remove_item=None, subject=None):
    if add_item and remove_item:
        add_name = add_item.get("name") or add_item.get("ts_code", "-")
        remove_name = remove_item.get("name") or remove_item.get("ts_code", "-")
        return f"调入 {add_name} / 调出 {remove_name}"
    if subject:
        return f"复核 {subject.get('name') or subject.get('ts_code', '-')}"
    return "组合动作建议"


def summarize_swap_status(gate_status):
    if gate_status == "ready":
        return "这组方案已通过当前参照层门禁，可以进入受控试单前检查。"
    if gate_status == "watch_only":
        return "这组方案先作为观察单，等待调入腿进入推荐池后再升级。"
    return "这组方案当前被门禁拦住，先解决阻塞项。"


def swap_priority(gate_status):
    if gate_status == "ready":
        return "high"
    if gate_status == "watch_only":
        return "medium"
    return "low"


def transcript_summary_text(item):
    transcript = (item or {}).get("public_transcript") or {}
    return transcript.get("summary")


def transcript_risk_text(item):
    transcript = (item or {}).get("public_transcript") or {}
    freshness = transcript.get("freshness_label")
    if freshness in {"missing", "stale"}:
        return "缺少足够新的电话会原话锚点，管理层最新表述还没完全核对。"
    return None


def transcript_next_check_text(item):
    transcript = (item or {}).get("public_transcript") or {}
    freshness = transcript.get("freshness_label")
    if freshness in {"fresh", "usable"}:
        return "复核最近电话会原话，确认管理层对订单、指引和节奏的表述是否支持这条动作。"
    if freshness in {"missing", "stale"}:
        return "补最近电话会文字稿或管理层原话锚点，避免动作建议只靠价格和二手研究。"
    return None


def transcript_source_ref(item):
    transcript = (item or {}).get("public_transcript") or {}
    return transcript.get("source_rel_path")


def capital_flow_summary_text(item):
    return ((item or {}).get("capital_flow_summary") or None)


def event_summary_text(item):
    return ((item or {}).get("event_summary") or None)


def auxiliary_watchpoint_text(item):
    return (((item or {}).get("auxiliary_watchpoints") or [None])[0])


def stock_connect_risk_text(item):
    frequencies = set((((item or {}).get("stock_connect") or {}).get("frequencies") or []))
    if "quarterly" in frequencies:
        return "互联互通持仓这里更多还是季频快照，不能把它直接当成短线资金表态。"
    return None


def build_swap_actions(execution_payload, execution_rel_path):
    actions = []
    for plan in (execution_payload.get("plans") or [])[:3]:
        add_item = plan.get("add") or {}
        remove_item = plan.get("remove") or {}
        gate = plan.get("gate_result") or {}
        uplift = plan.get("uplift") or {}
        gate_status = gate.get("status") or "unknown"
        actions.append(
            {
                "action_id": f"{gate_status}__{plan.get('plan_id')}",
                "action_type": {
                    "ready": "swap_ready",
                    "watch_only": "swap_watch",
                }.get(gate_status, "swap_blocked"),
                "priority": swap_priority(gate_status),
                "title": action_title(add_item=add_item, remove_item=remove_item),
                "summary": summarize_swap_status(gate_status),
                "gate_status": gate_status,
                "trade_amount": plan.get("trade_amount"),
                "trade_amount_pct": plan.get("trade_amount_pct"),
                "add": {
                    "ts_code": add_item.get("ts_code"),
                    "name": add_item.get("name"),
                    "sector": add_item.get("sector"),
                },
                "remove": {
                    "ts_code": remove_item.get("ts_code"),
                    "name": remove_item.get("name"),
                    "sector": remove_item.get("sector"),
                },
                "rationale": ordered_unique(
                    [
                        *(plan.get("expected_positive_change") or [])[:3],
                        uplift.get("summary"),
                        capital_flow_summary_text(add_item),
                        event_summary_text(add_item),
                        (add_item.get("official_material") or {}).get("summary"),
                        transcript_summary_text(add_item),
                        (add_item.get("public_analyst_signal") or {}).get("summary"),
                        f"调出腿当前客观看法：{display_label(remove_item.get('objective_view') or '-')}。",
                    ]
                )[:4],
                "risk_flags": ordered_unique(
                    [*(plan.get("risk_flags") or []), transcript_risk_text(add_item), stock_connect_risk_text(add_item)]
                )[:3],
                "next_checks": ordered_unique(
                    [*(plan.get("execution_checklist") or []), transcript_next_check_text(add_item), auxiliary_watchpoint_text(add_item)]
                )[:4],
                "source_refs": ordered_unique(
                    [
                        execution_rel_path,
                        (add_item.get("external_research") or {}).get("source_rel_path"),
                        (remove_item.get("external_research") or {}).get("source_rel_path"),
                        transcript_source_ref(add_item),
                        transcript_source_ref(remove_item),
                        (add_item.get("public_analyst_signal") or {}).get("source_rel_path"),
                        (remove_item.get("public_analyst_signal") or {}).get("source_rel_path"),
                        *((add_item.get("official_material") or {}).get("source_rel_paths") or [])[:2],
                        *((remove_item.get("official_material") or {}).get("source_rel_paths") or [])[:2],
                    ]
                ),
            }
        )
    return actions


def holding_watch_score(strategy_item, objective_item):
    score = 0.0
    objective_view = (objective_item or strategy_item or {}).get("objective_view")
    priority = ((strategy_item or {}).get("priority") or {}).get("label")
    research_state = ((strategy_item or {}).get("research_staleness") or {}).get("label")
    valuation = ((strategy_item or {}).get("valuation_pressure") or {}).get("label")
    signal_tags = set((strategy_item or {}).get("signal_tags") or [])

    score += {"repair_needed": 4.0, "observe": 2.5, "trend_positive": 1.0, "trend_follow": 0.5}.get(objective_view, 0.0)
    score += {"high": 2.0, "medium": 1.0, "low": 0.0}.get(priority, 0.0)
    score += {"missing": 1.5, "stale": 1.2, "aging": 0.6, "usable": 0.3, "fresh": 0.0}.get(research_state, 0.0)
    score += {"high": 1.2, "medium": 0.5}.get(valuation, 0.0)
    if "earnings_pressure" in signal_tags:
        score += 1.0
    if "short_term_hot" in signal_tags:
        score += 0.5
    return round(score, 2)


def build_holding_watch_actions(strategy_payload, objective_payload, covered_remove_codes, objective_rel_path, strategy_rel_path):
    objective_map = {item.get("ts_code"): item for item in (objective_payload.get("items") or []) if item.get("ts_code")}
    candidates = []
    for item in strategy_payload.get("items") or []:
        ts_code = item.get("ts_code")
        if not ts_code:
            continue
        if "portfolio_seed" not in set(item.get("pool_types") or []):
            continue
        if ts_code in covered_remove_codes:
            continue
        objective_item = objective_map.get(ts_code) or {}
        score = holding_watch_score(item, objective_item)
        if score < 3.5:
            continue
        objective_view = objective_item.get("objective_view") or item.get("objective_view")
        priority = "high" if score >= 5.5 else "medium"
        summary = (
            "先确认结构修复有没有真正发生，再决定是否要影响组合动作。"
            if objective_view == "repair_needed"
            else "趋势还没坏，但要重点盯业绩兑现、估值和研究新鲜度。"
        )
        candidates.append(
            (
                score,
                {
                    "action_id": f"holding_watch__{ts_code}",
                    "action_type": "holding_watch",
                    "priority": priority,
                    "title": action_title(subject=item),
                    "summary": summary,
                    "subject": {
                        "ts_code": ts_code,
                        "name": item.get("name"),
                        "sector": item.get("sector"),
                    },
                    "rationale": ordered_unique(
                        [
                            (item.get("trend_state") or {}).get("summary"),
                            (item.get("valuation_pressure") or {}).get("summary"),
                            (item.get("research_staleness") or {}).get("summary"),
                            capital_flow_summary_text(item),
                            event_summary_text(item),
                            (item.get("official_material") or {}).get("summary"),
                            transcript_summary_text(item),
                            (item.get("public_analyst_signal") or {}).get("summary"),
                            *((objective_item.get("watchpoints") or [])[:1]),
                        ]
                    )[:4],
                    "risk_flags": ordered_unique(
                        [
                            *((item.get("watchpoints") or [])[:2]),
                            auxiliary_watchpoint_text(item),
                            transcript_risk_text(item),
                            stock_connect_risk_text(item),
                            "当前仍是持仓参照层，不代表真实减仓指令。",
                        ]
                    )[:3],
                    "next_checks": ordered_unique(
                        [*((item.get("next_check_items") or [])[:4]), transcript_next_check_text(item), auxiliary_watchpoint_text(item)]
                    )[:4],
                    "source_refs": ordered_unique(
                        [
                            strategy_rel_path,
                            objective_rel_path,
                            item.get("card_rel_path"),
                            (item.get("external_research") or {}).get("source_rel_path"),
                            transcript_source_ref(item),
                            (item.get("public_analyst_signal") or {}).get("source_rel_path"),
                            *((item.get("official_material") or {}).get("source_rel_paths") or [])[:2],
                        ]
                    ),
                },
            )
        )
    candidates.sort(key=lambda item: (-item[0], item[1]["action_id"]))
    return [item[1] for item in candidates[:2]]


def opportunity_followup_score(item):
    primary_pool = item.get("primary_pool") or "none"
    score = safe_float(item.get("rotation_in_score")) or 0.0
    score += {"recommended": 1.0, "candidate": 0.4}.get(primary_pool, 0.0)
    return round(score, 2)


def build_opportunity_followups(rotation_payload, covered_add_codes, rotation_rel_path):
    candidates = []
    for item in rotation_payload.get("top_add_candidates") or []:
        ts_code = item.get("ts_code")
        if not ts_code or ts_code in covered_add_codes:
            continue
        score = opportunity_followup_score(item)
        if score <= 0:
            continue
        primary_pool = item.get("primary_pool") or "none"
        candidates.append(
            (
                score,
                {
                    "action_id": f"opportunity_followup__{ts_code}",
                    "action_type": "opportunity_followup",
                    "priority": "medium" if primary_pool == "recommended" else "low",
                    "title": f"继续跟踪候选 {(item.get('name') or ts_code)}",
                    "summary": "这只票还没进入本轮优先换仓对，但仍是后备机会位。",
                    "subject": {
                        "ts_code": ts_code,
                        "name": item.get("name"),
                        "sector": item.get("sector"),
                    },
                    "rationale": ordered_unique(
                        [
                            f"机会池层级：{display_label(primary_pool)}。",
                            (item.get("trend_state") or {}).get("summary"),
                            (item.get("research_staleness") or {}).get("summary"),
                            capital_flow_summary_text(item),
                            event_summary_text(item),
                            (item.get("official_material") or {}).get("summary"),
                            transcript_summary_text(item),
                            (item.get("public_analyst_signal") or {}).get("summary"),
                        ]
                    )[:4],
                    "risk_flags": ordered_unique(
                        [
                            *((item.get("watchpoints") or [])[:2]),
                            auxiliary_watchpoint_text(item),
                            transcript_risk_text(item),
                            stock_connect_risk_text(item),
                            (item.get("valuation_pressure") or {}).get("summary"),
                        ]
                    )[:3],
                    "next_checks": ordered_unique(
                        [*((item.get("next_check_items") or [])[:4]), transcript_next_check_text(item), auxiliary_watchpoint_text(item)]
                    )[:4],
                    "source_refs": ordered_unique(
                        [
                            rotation_rel_path,
                            (item.get("external_research") or {}).get("source_rel_path"),
                            transcript_source_ref(item),
                            (item.get("public_analyst_signal") or {}).get("source_rel_path"),
                            *((item.get("official_material") or {}).get("source_rel_paths") or [])[:2],
                        ]
                    ),
                },
            )
        )
    candidates.sort(key=lambda item: (-item[0], item[1]["action_id"]))
    return [item[1] for item in candidates[:2]]


def build_primary_call(mode, actions):
    lines = []
    if mode == "reference_only":
        lines.append("当前仍是参照层建议模式，这份建议稿基于持仓参照层，不代表真实账户自动下单。")
    else:
        lines.append("当前已进入真实仓位模式，这份建议稿可作为正式执行前的收敛清单。")

    ready_actions = [item for item in actions if item.get("action_type") == "swap_ready"]
    watch_actions = [item for item in actions if item.get("action_type") == "swap_watch"]
    holding_actions = [item for item in actions if item.get("action_type") == "holding_watch"]
    follow_actions = [item for item in actions if item.get("action_type") == "opportunity_followup"]

    if ready_actions:
        lines.append(
            "优先推进 "
            + " / ".join(action["title"] for action in ready_actions[:2])
            + "，先按受控试单前检查推进。"
        )
    elif watch_actions:
        lines.append("当前没有可推进动作，先把观察换仓单作为主跟踪对象。")
    else:
        lines.append("当前没有明确换仓动作，先以跟踪和复核为主。")

    if watch_actions:
        lines.append("仍有观察换仓单待触发，核心看调入腿能否升到推荐池。")
    if holding_actions:
        lines.append("未进入换仓对的持仓参照层，也要继续复核趋势、估值和研究新鲜度。")
    if follow_actions:
        lines.append("机会池里还有后备票需要继续跟踪，避免只盯当前持仓。")
    return lines[:4]


def render_action_block(lines, action):
    priority = PRIORITY_LABELS.get(action.get("priority"), action.get("priority") or "-")
    lines.extend(
        [
            f"### [{priority}] {action.get('title') or '-'}",
            "",
            f"- action_type: {ACTION_TYPE_LABELS.get(action.get('action_type'), '-')}",
            f"- summary: {action.get('summary') or '-'}",
        ]
    )
    if action.get("gate_status"):
        lines.append(f"- gate_status: {display_label(action.get('gate_status'))}")
    if action.get("trade_amount") is not None:
        lines.append(f"- trade_amount: `{action.get('trade_amount')}`")
    if action.get("trade_amount_pct") is not None:
        lines.append(f"- trade_amount_pct: `{action.get('trade_amount_pct')}`")
    add_item = action.get("add") or {}
    remove_item = action.get("remove") or {}
    subject = action.get("subject") or {}
    if add_item:
        lines.append(f"- 调入腿: `{add_item.get('ts_code') or '-'} {add_item.get('name') or ''}`")
    if remove_item:
        lines.append(f"- 调出腿: `{remove_item.get('ts_code') or '-'} {remove_item.get('name') or ''}`")
    if subject:
        lines.append(f"- 对象: `{subject.get('ts_code') or '-'} {subject.get('name') or ''}`")
    lines.extend(["", "#### 支撑理由", ""])
    for item in action.get("rationale") or ["当前没有额外支撑理由。"]:
        lines.append(f"- {item}")
    lines.extend(["", "#### 主要风险", ""])
    for item in action.get("risk_flags") or ["当前没有额外风险说明。"]:
        lines.append(f"- {item}")
    lines.extend(["", "#### 下一步检查", ""])
    for item in action.get("next_checks") or ["保持观察。"]:
        lines.append(f"- {item}")
    lines.extend(["", "#### 来源锚点", ""])
    for item in action.get("source_refs") or ["-"]:
        lines.append(f"- `{item}`")
    lines.append("")


def write_action_memo(path, created_at, action_date, payload, relationships):
    lines = [
        "# SMR 组合动作建议稿",
        "",
        f"- created_at: {created_at}",
        f"- action_date: {action_date}",
        f"- action_mode: {display_label(payload.get('action_mode') or '-')}",
        f"- action_count: `{payload.get('action_count', 0)}`",
        f"- priority_counts: {format_count_map(payload.get('priority_counts') or {})}",
        f"- action_type_counts: {format_count_map(payload.get('action_type_counts') or {})}",
        "",
        "## 来源层",
        "",
        f"- objective_monitor_rel_path: `{relationships.get('objective_monitor_rel_path') or '-'}`",
        f"- strategy_watch_rel_path: `{relationships.get('strategy_watch_rel_path') or '-'}`",
        f"- rotation_snapshot_rel_path: `{relationships.get('rotation_snapshot_rel_path') or '-'}`",
        f"- execution_plan_rel_path: `{relationships.get('execution_plan_rel_path') or '-'}`",
        "",
        "## 今日主张",
        "",
    ]
    for item in payload.get("primary_call") or ["当前没有生成明确主张。"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 优先动作清单", ""])
    if not payload.get("actions"):
        lines.append("- 当前没有可执行的组合动作建议。")
        lines.append("")
    else:
        for action in payload.get("actions") or []:
            render_action_block(lines, action)
    lines.extend(
        [
            "## 边界说明",
            "",
            "- 这层是把已有研究与组合约束收敛成动作清单，不是自动交易指令。",
            "- 如果还没补真实 `position`，所有金额和节奏都只能按参照层理解。",
            "- 真正执行前，仍要叠加 `entry.py / pnl.py / risk_monitor_snapshot` 的正式门禁。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_action_log(path, created_at, action_date, payload, relationships):
    action_type_counts = payload.get("action_type_counts") or {}
    lines = [
        "# SMR 组合动作日志",
        "",
        f"- created_at: {created_at}",
        f"- action_date: {action_date}",
        f"- action_mode: {display_label(payload.get('action_mode') or '-')}",
        f"- action_count: `{payload.get('action_count', 0)}`",
        f"- action_type_counts: {format_count_map(action_type_counts)}",
        f"- execution_precheck_rel_path: `{relationships.get('execution_precheck_rel_path') or '-'}`",
        f"- objective_monitor_rel_path: `{relationships.get('objective_monitor_rel_path') or '-'}`",
        f"- strategy_watch_rel_path: `{relationships.get('strategy_watch_rel_path') or '-'}`",
        f"- rotation_snapshot_rel_path: `{relationships.get('rotation_snapshot_rel_path') or '-'}`",
        f"- execution_plan_rel_path: `{relationships.get('execution_plan_rel_path') or '-'}`",
        "",
        "## 今日主张",
        "",
    ]
    for line in payload.get("primary_call") or ["当前没有明确主张。"]:
        lines.append(f"- {line}")
    lines.extend(["", "## 动作摘要", ""])
    for action in payload.get("actions") or []:
        lines.append(
            f"- {action.get('title') or '-'}｜{ACTION_TYPE_LABELS.get(action.get('action_type'), action.get('action_type') or '-')}"
            f"｜优先级 {PRIORITY_LABELS.get(action.get('priority'), action.get('priority') or '-')}"
            f"｜{action.get('summary') or '-'}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a portfolio action memo from current portfolio layers")
    parser.add_argument("--date", help="Prefer snapshots for this entity_id date")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)

    execution_entry = load_snapshot_entry(conn, "rotation_execution_plan_snapshot", args.date, required=True)
    action_date = execution_entry.get("entity_id")
    strategy_entry = load_snapshot_entry(conn, "strategy_watch_batch", action_date, required=True)
    objective_entry = load_snapshot_entry(conn, "stock_objective_monitor_snapshot", action_date, required=True)
    rotation_entry = load_snapshot_entry(conn, "rotation_candidate_snapshot", action_date, required=True)

    execution_payload = execution_entry.get("payload", {}) or {}
    strategy_payload = strategy_entry.get("payload", {}) or {}
    objective_payload = objective_entry.get("payload", {}) or {}
    rotation_payload = rotation_entry.get("payload", {}) or {}
    build_execution_precheck_for_date(conn, action_date, created_at=created_at)
    precheck_entry = load_snapshot_entry(conn, "execution_precheck_snapshot", action_date, required=False)
    precheck_payload = (precheck_entry or {}).get("payload", {}) or {}

    relationships = {
        "summary_rel_path": None,
        "action_log_rel_path": None,
        "objective_monitor_rel_path": (objective_entry.get("relationships", {}) or {}).get("monitor_rel_path")
        or objective_payload.get("monitor_rel_path"),
        "strategy_watch_rel_path": (strategy_entry.get("relationships", {}) or {}).get("summary_rel_path")
        or strategy_payload.get("summary_rel_path"),
        "rotation_snapshot_rel_path": (rotation_entry.get("relationships", {}) or {}).get("summary_rel_path")
        or rotation_payload.get("summary_rel_path"),
        "execution_plan_rel_path": (execution_entry.get("relationships", {}) or {}).get("summary_rel_path")
        or execution_payload.get("summary_rel_path"),
        "execution_precheck_rel_path": ((precheck_entry or {}).get("relationships", {}) or {}).get("summary_rel_path")
        or precheck_payload.get("summary_rel_path"),
        "objective_monitor_entry_id": objective_entry.get("id"),
        "strategy_watch_entry_id": strategy_entry.get("id"),
        "rotation_snapshot_entry_id": rotation_entry.get("id"),
        "execution_plan_entry_id": execution_entry.get("id"),
        "execution_precheck_entry_id": (precheck_entry or {}).get("id"),
    }

    swap_actions = build_swap_actions(execution_payload, relationships["execution_plan_rel_path"])
    covered_add_codes = {((item.get("add") or {}).get("ts_code")) for item in swap_actions if item.get("add")}
    covered_remove_codes = {((item.get("remove") or {}).get("ts_code")) for item in swap_actions if item.get("remove")}
    holding_actions = build_holding_watch_actions(
        strategy_payload,
        objective_payload,
        covered_remove_codes,
        relationships["objective_monitor_rel_path"],
        relationships["strategy_watch_rel_path"],
    )
    followup_actions = build_opportunity_followups(
        rotation_payload,
        covered_add_codes,
        relationships["rotation_snapshot_rel_path"],
    )

    actions = swap_actions + holding_actions + followup_actions
    priority_counts = Counter(item.get("priority", "unknown") for item in actions)
    action_type_counts = Counter(item.get("action_type", "unknown") for item in actions)
    payload = {
        "action_mode": execution_payload.get("plan_mode"),
        "action_count": len(actions),
        "priority_counts": dict(priority_counts),
        "action_type_counts": dict(action_type_counts),
        "primary_call": build_primary_call(execution_payload.get("plan_mode"), actions),
        "summary_rel_path": None,
        "action_log_rel_path": None,
        "execution_precheck_status": precheck_payload.get("precheck_status"),
        "actions": actions,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{action_date}_portfolio_action_memo.md"
    action_log_path = LOG_DIR / f"{action_date}_portfolio_action_log.md"
    relationships["summary_rel_path"] = relative_to_project(output_path)
    relationships["action_log_rel_path"] = relative_to_project(action_log_path)
    payload["summary_rel_path"] = relative_to_project(output_path)
    payload["action_log_rel_path"] = relative_to_project(action_log_path)
    write_action_memo(output_path, created_at, action_date, payload, relationships)
    write_action_log(action_log_path, created_at, action_date, payload, relationships)

    entry = register_snapshot(
        conn,
        entity_type="portfolio_action_memo_snapshot",
        entity_id=action_date,
        status="generated" if actions else "empty",
        source="build_portfolio_action_memo.py",
        relationships=relationships,
        payload=payload,
        created_at=created_at,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="组合动作建议稿已更新，自动转交 Hermes-like 研究代理补充解释并同步调度。",
        created_by="build_portfolio_action_memo.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "build_portfolio_action_memo.py",
        "success",
        "portfolio action memo built",
        {
            "entity_id": action_date,
            "action_mode": payload.get("action_mode"),
            "action_count": len(actions),
            "summary_rel_path": relative_to_project(output_path),
            "action_log_rel_path": relative_to_project(action_log_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Portfolio action memo snapshot registered: {action_date}")
    print(f"Summary file: {output_path}")
    print(f"Action log: {action_log_path}")
    print(f"Action mode: {payload.get('action_mode')}")
    print(f"Action count: {len(actions)}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
