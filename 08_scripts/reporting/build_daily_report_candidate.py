#!/usr/bin/env python3
"""Compile a human-readable daily report candidate from the latest reporting snapshot."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, ensure_auto_handoff, get_latest_registry_entry
from smr_flow_event_digest import build_market_context_digest
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_reporting_priority import build_high_value_reporting_digest
from smr_runlog import log_run

OUTPUT_DIR = env_or_project_path("SMR_DAILY_REPORT_CANDIDATE_DIR", "06_reports", "daily_candidates")

SOURCE_FAMILY_LABELS = {
    "official_material": "官方一手",
    "public_transcript": "电话会原话",
    "public_analyst_signal": "公开卖方信号",
    "external_research": "二手研究",
}

GATE_STATUS_LABELS = {
    "ready": "可推进",
    "watch_only": "先观察",
    "blocked": "被门禁拦住",
}

DISPLAY_LABELS = {
    "trend_follow": "趋势跟随",
    "trend_positive": "趋势偏正",
    "observe": "观察",
    "repair_needed": "等待修复",
}


def load_daily_reporting_entry(conn, entity_id=None):
    if entity_id:
        entry = get_latest_registry_entry(conn, "daily_reporting_snapshot", entity_id)
        if entry is None:
            raise SystemExit(f"daily_reporting_snapshot not found for entity_id: {entity_id}")
        return entry

    row = conn.execute(
        """
        SELECT entity_id
        FROM task_registry_entity_latest
        WHERE entity_type='daily_reporting_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        raise SystemExit("daily_reporting_snapshot not found")
    entry = get_latest_registry_entry(conn, "daily_reporting_snapshot", row[0])
    if entry is None:
        raise SystemExit("latest daily_reporting_snapshot entry missing")
    return entry


def ordered_unique(values):
    seen = set()
    rows = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def display_label(value):
    if value in (None, ""):
        return "-"
    return DISPLAY_LABELS.get(str(value), str(value))


def collect_focus_items(payload):
    items = []
    strategy_payload = payload.get("strategy_watch_batch") or {}
    action_payload = payload.get("portfolio_action_memo_snapshot") or {}
    for item in (strategy_payload.get("top_focus_items") or [])[:4]:
        items.append({"ts_code": item.get("ts_code"), "name": item.get("name")})
    for action in (action_payload.get("actions") or [])[:3]:
        subject = action.get("subject") or action.get("add") or {}
        if subject.get("ts_code"):
            items.append({"ts_code": subject.get("ts_code"), "name": subject.get("name")})
    unique = []
    seen = set()
    for item in items:
        ts_code = item.get("ts_code")
        if not ts_code or ts_code in seen:
            continue
        seen.add(ts_code)
        unique.append(item)
    return unique[:5]


def build_overview_lines(payload, market_context=None):
    action_payload = payload.get("portfolio_action_memo_snapshot") or {}
    strategy_payload = payload.get("strategy_watch_batch") or {}
    rotation_payload = payload.get("rotation_candidate_snapshot") or {}
    lines = []
    for value in (action_payload.get("primary_call") or [])[:3]:
        lines.append(value)
    for item in (strategy_payload.get("top_focus_items") or [])[:2]:
        trend_state = (item.get("trend_state") or {}).get("summary")
        name = item.get("name") or item.get("ts_code") or "-"
        if trend_state:
            lines.append(f"{name} 继续重点盯，原因是 {trend_state}")
    for pair in (rotation_payload.get("rotation_pairs") or [])[:1]:
        add_item = pair.get("add") or {}
        remove_item = pair.get("remove") or {}
        if add_item.get("ts_code") and remove_item.get("ts_code"):
            lines.append(
                f"轮动层当前最强的一组还是调入 {add_item.get('name') or add_item.get('ts_code')}，"
                f"对应调出 {remove_item.get('name') or remove_item.get('ts_code')}。"
            )
    for value in ((market_context or {}).get("capital_flow_lines") or [])[:1]:
        lines.append(value)
    for value in ((market_context or {}).get("event_lines") or [])[:1]:
        lines.append(value)
    return ordered_unique(lines)[:5]


def build_action_lines(payload):
    action_payload = payload.get("portfolio_action_memo_snapshot") or {}
    actions = action_payload.get("actions") or []
    lines = []
    for action in actions[:5]:
        gate_status = GATE_STATUS_LABELS.get(action.get("gate_status"), action.get("gate_status") or "继续观察")
        rationale = (action.get("rationale") or [None])[0]
        lines.append(
            {
                "title": action.get("title") or "-",
                "gate_status": gate_status,
                "summary": action.get("summary") or "-",
                "rationale": rationale or "-",
            }
        )
    return lines


def build_watch_lines(payload, market_context=None):
    strategy_payload = payload.get("strategy_watch_batch") or {}
    digest_by_code = {
        item.get("ts_code"): item
        for item in ((market_context or {}).get("focus_symbol_digests") or [])
        if item.get("ts_code")
    }
    rows = []
    for item in (strategy_payload.get("top_focus_items") or [])[:5]:
        fresh_digest = digest_by_code.get(item.get("ts_code")) or {}
        rows.append(
            {
                "name": item.get("name") or item.get("ts_code") or "-",
                "ts_code": item.get("ts_code") or "-",
                "objective_view": display_label(item.get("objective_view")),
                "trend_summary": (item.get("trend_state") or {}).get("summary") or "-",
                "watchpoint": ((fresh_digest.get("watchpoints") or item.get("watchpoints") or [None])[0]) or "-",
                "capital_flow_summary": fresh_digest.get("capital_flow_summary") or item.get("capital_flow_summary") or "-",
                "event_summary": fresh_digest.get("event_summary") or item.get("event_summary") or "-",
            }
        )
    return rows


def build_capital_flow_lines(payload, market_context):
    strategy_payload = payload.get("strategy_watch_batch") or {}
    lines = list((market_context or {}).get("capital_flow_lines") or [])
    digest_by_code = {
        item.get("ts_code"): item
        for item in ((market_context or {}).get("focus_symbol_digests") or [])
        if item.get("ts_code")
    }
    for item in (strategy_payload.get("top_focus_items") or [])[:3]:
        fresh_digest = digest_by_code.get(item.get("ts_code")) or {}
        summary = fresh_digest.get("capital_flow_summary") or item.get("capital_flow_summary")
        name = item.get("name") or item.get("ts_code")
        if summary and name:
            lines.append(f"{name}：{summary}")
    return ordered_unique(lines)[:6]


def build_event_lines(payload, market_context):
    strategy_payload = payload.get("strategy_watch_batch") or {}
    lines = list((market_context or {}).get("event_lines") or [])
    digest_by_code = {
        item.get("ts_code"): item
        for item in ((market_context or {}).get("focus_symbol_digests") or [])
        if item.get("ts_code")
    }
    for item in (strategy_payload.get("top_focus_items") or [])[:3]:
        fresh_digest = digest_by_code.get(item.get("ts_code")) or {}
        summary = fresh_digest.get("event_summary") or item.get("event_summary")
        name = item.get("name") or item.get("ts_code")
        if summary and name:
            lines.append(f"{name}：{summary}")
    return ordered_unique(lines)[:4]


def build_market_flow_anomaly_lines(payload):
    snapshot = payload.get("market_flow_anomaly_snapshot") or {}
    coverage = snapshot.get("coverage_summary") or {}
    markets = snapshot.get("markets") or {}
    lines = []
    scope_note = coverage.get("scope_note")
    if scope_note:
        lines.append(scope_note)
    for market_code, market_label in (("A", "A股"), ("H", "港股"), ("US", "美股")):
        items = (markets.get(market_code) or [])[:3]
        for item in items:
            lines.append(
                f"{market_label} {item.get('name') or item.get('symbol') or '-'}："
                f"{item.get('reason_summary') or '出现明显量价异动'}；"
                f"最新资讯：{item.get('news_summary') or '暂无'}"
            )
    return ordered_unique(lines)[:10]


def build_risk_lines(payload):
    execution_payload = payload.get("rotation_execution_plan_snapshot") or {}
    action_payload = payload.get("portfolio_action_memo_snapshot") or {}
    risk_payload = payload.get("risk_monitor_snapshot") or {}
    risk_lines = []
    status_counts = execution_payload.get("status_counts") or {}
    blocked = status_counts.get("blocked", 0)
    watch_only = status_counts.get("watch_only", 0)
    if blocked:
        risk_lines.append(f"当前至少有 {blocked} 组执行方案被门禁拦住，不能把动作建议当成真执行指令。")
    if watch_only:
        risk_lines.append(f"还有 {watch_only} 组轮动方案只是观察单，核心触发点还是调入腿能否升到推荐池。")

    action_mode = action_payload.get("action_mode")
    if action_mode == "reference_only":
        risk_lines.append("当前还是参照层模式，金额和节奏只能理解成推演，不能当真实仓位动作。")

    high_value_digest = payload.get("high_value_reporting_digest") or {}
    families = {item.get("source_family") for item in (high_value_digest.get("items") or [])}
    if "public_transcript" not in families:
        risk_lines.append("当前高价值证据里还缺更硬的电话会原话，部分判断仍要更多依赖公告和价格结构。")
    for item in (risk_payload.get("reference_observations") or [])[:2]:
        risk_lines.append(f"参考组合观察：{item}")
    return ordered_unique(risk_lines)[:4]


def render_candidate_markdown(
    report_date,
    created_at,
    summary_lines,
    high_value_digest,
    capital_flow_lines,
    market_flow_anomaly_lines,
    event_lines,
    action_lines,
    watch_lines,
    risk_lines,
    relationships,
):
    lines = [
        "# SMR 盘前简报候选",
        "",
        f"- created_at: {created_at}",
        f"- report_date: {report_date}",
        f"- source_daily_reporting_snapshot_rel_path: `{relationships.get('daily_reporting_snapshot_rel_path') or '-'}`",
        f"- latest_report_rel_path: `{relationships.get('latest_report_rel_path') or '-'}`",
        f"- dispatch_board_rel_path: `{relationships.get('dispatch_board_rel_path') or '-'}`",
        "",
        "## 一句话结论",
        "",
    ]
    for line in summary_lines or ["当前先没有清晰主张，只能继续按监控链追踪。"]:
        lines.append(f"- {line}")

    lines.extend(["", "## 今日最该先看什么", ""])
    for item in (high_value_digest.get("items") or [])[:8]:
        source_family = SOURCE_FAMILY_LABELS.get(item.get("source_family"), item.get("source_family") or "-")
        lines.append(
            f"- {item.get('name') or item.get('ts_code') or '-'} / {item.get('ts_code') or '-'}"
            f"｜{source_family}｜{item.get('headline') or item.get('summary') or '-'}"
        )

    lines.extend(["", "## 资金流补充", ""])
    for line in capital_flow_lines or ["当前还没有提炼出更强的资金流补充。"]:
        lines.append(f"- {line}")

    lines.extend(["", "## 全覆盖库资金异动", ""])
    for line in market_flow_anomaly_lines or ["当前还没有生成跨市场资金异动榜单。"]:
        lines.append(f"- {line}")

    lines.extend(["", "## 事件催化补充", ""])
    for line in event_lines or ["当前还没有提炼出更强的事件催化补充。"]:
        lines.append(f"- {line}")

    lines.extend(["", "## 组合动作收口", ""])
    if not action_lines:
        lines.append("- 当前没有生成明确动作，先保留观察。")
    else:
        for item in action_lines:
            lines.append(
                f"- {item['title']}｜{item['gate_status']}｜{item['summary']}｜支撑理由：{item['rationale']}"
            )

    lines.extend(["", "## 重点标的跟踪", ""])
    if not watch_lines:
        lines.append("- 当前没有提炼出重点标的。")
    else:
        for item in watch_lines:
            lines.append(
                f"- {item['name']} / {item['ts_code']}｜当前口径：{item['objective_view']}｜"
                f"{item['trend_summary']}｜资金面：{item['capital_flow_summary']}｜事件面：{item['event_summary']}｜观察点：{item['watchpoint']}"
            )

    lines.extend(["", "## 当前边界与风险", ""])
    for item in risk_lines or ["当前没有额外风险说明。"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 文件入口",
            "",
            f"- 策略观察：`{relationships.get('strategy_watch_rel_path') or '-'}`",
            f"- 轮动候选：`{relationships.get('rotation_snapshot_rel_path') or '-'}`",
            f"- 执行方案：`{relationships.get('execution_plan_rel_path') or '-'}`",
            f"- 动作建议：`{relationships.get('portfolio_action_rel_path') or '-'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_daily_report_candidate_for_snapshot(conn, snapshot_entry, created_at=None):
    created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = snapshot_entry.get("payload") or {}
    relationships = snapshot_entry.get("relationships") or {}
    report_date = snapshot_entry.get("entity_id")
    focus_items = collect_focus_items(payload)
    market_context = build_market_context_digest(conn, focus_items)
    capital_flow_fact_sheet = market_context.get("capital_flow_fact_sheet") or payload.get("capital_flow_fact_sheet") or {}
    market_flow_anomaly_lines = build_market_flow_anomaly_lines(payload)

    high_value_digest = payload.get("high_value_reporting_digest") or build_high_value_reporting_digest(
        payload.get("external_research_digest") or {},
        payload.get("official_material_digest") or {},
        payload.get("public_transcript_digest") or {},
        payload.get("public_analyst_signal_digest") or {},
    )
    summary_lines = build_overview_lines(payload, market_context)
    capital_flow_lines = build_capital_flow_lines(payload, market_context)
    event_lines = build_event_lines(payload, market_context)
    action_lines = build_action_lines(payload)
    watch_lines = build_watch_lines(payload, market_context)
    risk_lines = build_risk_lines(payload)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{report_date}_盘前简报_candidate.md"
    candidate_relationships = {
        "candidate_rel_path": relative_to_project(output_path),
        "daily_reporting_snapshot_rel_path": relationships.get("latest_report_rel_path"),
        "latest_report_rel_path": relationships.get("latest_report_rel_path"),
        "dispatch_board_rel_path": relationships.get("dispatch_board_rel_path"),
        "strategy_watch_rel_path": ((payload.get("strategy_watch_batch") or {}).get("summary_rel_path")),
        "rotation_snapshot_rel_path": ((payload.get("rotation_candidate_snapshot") or {}).get("summary_rel_path")),
        "execution_plan_rel_path": ((payload.get("rotation_execution_plan_snapshot") or {}).get("summary_rel_path")),
        "portfolio_action_rel_path": ((payload.get("portfolio_action_memo_snapshot") or {}).get("summary_rel_path")),
        "daily_reporting_snapshot_entry_id": snapshot_entry.get("id"),
    }

    output_path.write_text(
        render_candidate_markdown(
            report_date,
            created_at,
            summary_lines,
            high_value_digest,
            capital_flow_lines,
            market_flow_anomaly_lines,
            event_lines,
            action_lines,
            watch_lines,
            risk_lines,
            candidate_relationships,
        ),
        encoding="utf-8",
    )

    candidate_summary = " ".join(summary_lines[:3]).strip()
    candidate_payload = {
        "candidate_title": f"SMR 盘前简报候选 {report_date}",
        "candidate_summary": candidate_summary,
        "candidate_rel_path": relative_to_project(output_path),
        "overview_lines": summary_lines,
        "capital_flow_fact_sheet": capital_flow_fact_sheet,
        "high_value_reporting_digest": high_value_digest,
        "capital_flow_digest": capital_flow_lines,
        "market_flow_anomaly_digest": market_flow_anomaly_lines,
        "event_digest": event_lines,
        "action_digest": action_lines,
        "watch_digest": watch_lines,
        "risk_digest": risk_lines,
        "source_daily_reporting_snapshot_entry_id": snapshot_entry.get("id"),
    }
    entry = register_snapshot(
        conn,
        entity_type="daily_report_candidate",
        entity_id=report_date,
        status="generated",
        source="build_daily_report_candidate.py",
        relationships=candidate_relationships,
        payload=candidate_payload,
        created_at=created_at,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="日报候选稿已生成，自动转交 Hermes-like 日报代理继续压缩与补注。",
        created_by="build_daily_report_candidate.py",
    )
    return {
        "entry": entry,
        "output_path": output_path,
        "candidate_payload": candidate_payload,
        "handoff_result": handoff_result,
    }


def main():
    parser = argparse.ArgumentParser(description="Build daily report candidate from daily_reporting_snapshot")
    parser.add_argument("--date", help="daily_reporting_snapshot entity_id date")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    snapshot_entry = load_daily_reporting_entry(conn, args.date)
    result = build_daily_report_candidate_for_snapshot(conn, snapshot_entry)
    conn.commit()
    conn.close()

    log_run(
        "build_daily_report_candidate.py",
        "success",
        "daily report candidate built",
        {
            "entity_id": snapshot_entry.get("entity_id"),
            "candidate_rel_path": relative_to_project(result["output_path"]),
            "handoff_result": result["handoff_result"]["reason"],
            "handoff_id": result["handoff_result"]["handoff"]["handoff_id"]
            if result["handoff_result"]["handoff"]
            else None,
        },
    )
    print(f"Daily report candidate built: {snapshot_entry.get('entity_id')}")
    print(f"Candidate file: {result['output_path']}")
    if result["handoff_result"]["handoff"]:
        print(
            f"Auto handoff {result['handoff_result']['reason']}: "
            f"{result['handoff_result']['handoff']['handoff_id']} -> "
            f"{result['handoff_result']['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {result['handoff_result']['reason']}")


if __name__ == "__main__":
    main()
