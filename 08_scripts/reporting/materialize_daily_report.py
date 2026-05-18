#!/usr/bin/env python3
"""Materialize a polished formal daily report from the current snapshot and candidate."""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_trade_calendar import expected_trade_dates, format_date

REPORT_DIR = env_or_project_path("SMR_DAILY_REPORT_DIR", "06_reports", "daily")
PUBLISH_QUEUE_DIR = env_or_project_path("SMR_PUBLISH_QUEUE_DIR", "07_publish", "queue")

SOURCE_FAMILY_LABELS = {
    "official_material": "官方一手",
    "public_transcript": "电话会原话",
    "public_analyst_signal": "公开卖方信号",
    "external_research": "二手研究",
}


def load_entry(conn, entity_type, entity_id):
    entry = get_latest_registry_entry(conn, entity_type, entity_id)
    if entry is None:
        raise SystemExit(f"{entity_type} not found for entity_id: {entity_id}")
    return entry


def latest_available_report_date(conn):
    row = conn.execute(
        """
        SELECT entity_id
        FROM task_registry_entity_latest
        WHERE entity_type='daily_reporting_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row or not row[0]:
        raise SystemExit("daily_reporting_snapshot not found")
    return row[0]
def first_non_empty(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def compact_text(value, limit=None):
    text = str(value or "").strip()
    text = text.replace("\n", " ").replace("|", "/") if text else "-"
    if limit is not None and text not in {"-", ""} and len(text) > limit:
        return f"{text[: limit - 1].rstrip()}…"
    return text


def render_conclusion(overview_lines):
    lines = overview_lines or ["当前没有收敛出更强的新主张，先继续按监控链推进。"]
    return [f"- {line}" for line in lines]


def render_priority_table(high_value_digest):
    items = (high_value_digest or {}).get("items") or []
    lines = [
        "| 优先级 | 标的 | 证据类型 | 核心要点 |",
        "| --- | --- | --- | --- |",
    ]
    for index, item in enumerate(items[:8], start=1):
        label = SOURCE_FAMILY_LABELS.get(item.get("source_family"), item.get("source_family") or "-")
        subject = f"{item.get('name') or item.get('ts_code') or '-'} / {item.get('ts_code') or '-'}"
        summary = compact_text(item.get("headline") or item.get("summary"))
        lines.append(f"| P{index} | {subject} | {label} | {summary} |")
    if len(lines) == 2:
        lines.append("| - | - | - | 当前没有可优先提炼的高价值证据。 |")
    return lines


def render_action_table(action_digest):
    lines = [
        "| 动作 | 当前状态 | 建议摘要 | 关键理由 |",
        "| --- | --- | --- | --- |",
    ]
    for item in (action_digest or [])[:5]:
        lines.append(
            "| {title} | {gate_status} | {summary} | {rationale} |".format(
                title=compact_text(item.get("title")),
                gate_status=compact_text(item.get("gate_status")),
                summary=compact_text(item.get("summary")),
                rationale=compact_text(item.get("rationale")),
            )
        )
    if len(lines) == 2:
        lines.append("| - | - | 当前没有明确动作。 | - |")
    return lines


def render_watch_table(watch_digest):
    lines = [
        "| 标的 | 当前口径 | 趋势判断 | 资金面 | 事件面 | 观察点 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in (watch_digest or [])[:5]:
        subject = f"{item.get('name') or '-'} / {item.get('ts_code') or '-'}"
        lines.append(
            "| {subject} | {objective_view} | {trend_summary} | {capital_flow_summary} | {event_summary} | {watchpoint} |".format(
                subject=compact_text(subject),
                objective_view=compact_text(item.get("objective_view")),
                trend_summary=compact_text(item.get("trend_summary")),
                capital_flow_summary=compact_text(item.get("capital_flow_summary")),
                event_summary=compact_text(item.get("event_summary")),
                watchpoint=compact_text(item.get("watchpoint")),
            )
        )
    if len(lines) == 2:
        lines.append("| - | - | 当前没有提炼出重点盯盘标的。 | - | - | - |")
    return lines


def render_digest_lines(items, fallback):
    rows = items or [fallback]
    return [f"- {compact_text(row)}" for row in rows]


def render_market_flow_table(snapshot):
    snapshot = snapshot or {}
    coverage = snapshot.get("coverage_summary") or {}
    markets = snapshot.get("markets") or {}
    lines = [
        f"- 扫描口径：{compact_text(coverage.get('scope_label') or '当前系统已覆盖库实时扫描')}",
        f"- 口径说明：{compact_text(coverage.get('scope_note') or '当前只覆盖已纳入系统数据库的标的，不代表三地市场全量。')}",
        "",
    ]
    for market_code, market_label in (("A", "A股"), ("H", "港股"), ("US", "美股")):
        items = markets.get(market_code) or []
        lines.extend(
            [
                f"### {market_label}资金异动",
                "",
                "| 标的 | 交易日 | 日涨跌 | 异动分数 | 最新资讯 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        if not items:
            lines.append("| - | - | - | - | 当前没有可展示的异动标的。 |")
            lines.append("")
            continue
        for item in items[:6]:
            lines.append(
                "| {subject} | {trade_date} | {pct} | {score} | {news} |".format(
                    subject=compact_text(f"{item.get('name') or '-'} / {item.get('symbol') or '-'}"),
                    trade_date=compact_text(item.get("trade_date")),
                    pct=compact_text(f"{(item.get('pct_chg') or 0.0):+.2f}%"),
                    score=compact_text(item.get("flow_signal_score")),
                    news=compact_text(item.get("news_summary"), 72),
                )
            )
        lines.append("")
    return lines


def render_risk_lines(risk_digest):
    rows = risk_digest or ["当前没有新增边界说明。"]
    return [f"- {compact_text(row)}" for row in rows]


def render_entry_links(relationships):
    return [
        f"- 策略观察：`{relationships.get('strategy_watch_rel_path') or '-'}`",
        f"- 轮动候选：`{relationships.get('rotation_snapshot_rel_path') or '-'}`",
        f"- 执行方案：`{relationships.get('execution_plan_rel_path') or '-'}`",
        f"- 动作建议：`{relationships.get('portfolio_action_rel_path') or '-'}`",
        f"- 调度面板：`{relationships.get('dispatch_board_rel_path') or '-'}`",
    ]


def render_capital_flow_header(capital_flow_fact_sheet):
    fact_sheet = capital_flow_fact_sheet or {}
    margin = fact_sheet.get("margin_balance") or {}
    stock_connect = fact_sheet.get("stock_connect") or {}
    if not margin and not stock_connect:
        return None
    return (
        f"**资金流随时**：两融 {margin.get('fact_trade_date') or '-'} | "
        f"互联互通日频 {stock_connect.get('fact_trade_date') or '-'} | "
        "互联互通持股按官方可得频率分别展示"
    )


def report_header_line(created_at, a_trade_date, hk_trade_date, us_trade_date):
    return (
        f"**撰写时间**：{created_at[11:16]} 上海 | "
        f"**A股实时锚点**：{a_trade_date} | "
        f"**港股实时锚点**：{hk_trade_date} | "
        f"**美股实时锚点**：{us_trade_date}"
    )


def render_report_markdown(
    report_date,
    created_at,
    a_trade_date,
    hk_trade_date,
    us_trade_date,
    capital_flow_fact_sheet,
    overview_lines,
    high_value_digest,
    capital_flow_digest,
    market_flow_anomaly_snapshot,
    event_digest,
    action_digest,
    watch_digest,
    risk_digest,
    relationships,
):
    capital_flow_header = render_capital_flow_header(capital_flow_fact_sheet)
    lines = [
        f"# 📋 SMR 盘前简报 | {report_date}",
        "",
        report_header_line(created_at, a_trade_date, hk_trade_date, us_trade_date),
        capital_flow_header or "",
        "",
        "---",
        "",
        "## 一、今日结论",
        "",
        *render_conclusion(overview_lines),
        "",
        "## 二、高价值信息优先级",
        "",
        *render_priority_table(high_value_digest),
        "",
        "## 三、资金流补充",
        "",
        *render_digest_lines(capital_flow_digest, "当前还没有提炼出更强的资金流补充。"),
        "",
        "## 四、全覆盖库资金异动",
        "",
        *render_market_flow_table(market_flow_anomaly_snapshot),
        "",
        "## 五、事件催化补充",
        "",
        *render_digest_lines(event_digest, "当前还没有提炼出更强的事件催化补充。"),
        "",
        "## 六、组合动作建议",
        "",
        *render_action_table(action_digest),
        "",
        "## 七、重点盯盘标的",
        "",
        *render_watch_table(watch_digest),
        "",
        "## 八、当前边界与风险",
        "",
        *render_risk_lines(risk_digest),
        "",
        "## 九、关键文件入口",
        "",
        *render_entry_links(relationships),
        "",
        "## 十、免责声明",
        "",
        "- 本报告仅供系统内部研究与复盘使用，不构成任何投资建议。",
        "- 当前若仍处于参照层模式，所有调仓金额和节奏都只代表推演，不代表真实账户自动执行。",
        "- 市场有风险，决策需结合你自己的账户状态、交易纪律和风险承受能力。",
        "",
    ]
    return "\n".join(lines)


def materialize_report(conn, report_date, enqueue_publish=False):
    snapshot_entry = load_entry(conn, "daily_reporting_snapshot", report_date)
    candidate_entry = load_entry(conn, "daily_report_candidate", report_date)

    snapshot_payload = snapshot_entry.get("payload") or {}
    candidate_payload = candidate_entry.get("payload") or {}
    candidate_relationships = candidate_entry.get("relationships") or {}

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    expected_trade = expected_trade_dates(now)
    a_trade_date = format_date(expected_trade["a_expected"]) or "-"
    hk_trade_date = format_date(expected_trade["hk_expected"]) or "-"
    us_trade_date = format_date(expected_trade["us_expected"]) or "-"

    report_text = render_report_markdown(
        report_date=report_date,
        created_at=created_at,
        a_trade_date=a_trade_date,
        hk_trade_date=hk_trade_date,
        us_trade_date=us_trade_date,
        capital_flow_fact_sheet=candidate_payload.get("capital_flow_fact_sheet")
        or snapshot_payload.get("capital_flow_fact_sheet")
        or {},
        overview_lines=candidate_payload.get("overview_lines") or [],
        high_value_digest=candidate_payload.get("high_value_reporting_digest") or snapshot_payload.get("high_value_reporting_digest") or {},
        capital_flow_digest=candidate_payload.get("capital_flow_digest") or [],
        market_flow_anomaly_snapshot=snapshot_payload.get("market_flow_anomaly_snapshot") or {},
        event_digest=candidate_payload.get("event_digest") or [],
        action_digest=candidate_payload.get("action_digest") or [],
        watch_digest=candidate_payload.get("watch_digest") or [],
        risk_digest=candidate_payload.get("risk_digest") or [],
        relationships=candidate_relationships,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"{report_date}_盘前简报.md"
    report_path.write_text(report_text + "\n", encoding="utf-8")

    publish_rel_path = None
    if enqueue_publish:
        PUBLISH_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        publish_path = PUBLISH_QUEUE_DIR / report_path.name
        shutil.copyfile(report_path, publish_path)
        publish_rel_path = relative_to_project(publish_path)

    entry = register_snapshot(
        conn,
        entity_type="daily_report_publish_execution",
        entity_id=report_date,
        status="published" if enqueue_publish else "materialized",
        source="materialize_daily_report.py",
        relationships={
            "daily_reporting_snapshot_entry_id": snapshot_entry.get("id"),
            "daily_report_candidate_entry_id": candidate_entry.get("id"),
            "report_rel_path": relative_to_project(report_path),
            "publish_queue_rel_path": publish_rel_path,
        },
        payload={
            "report_title": f"📋 SMR 盘前简报 | {report_date}",
            "a_trade_date": a_trade_date,
            "hk_trade_date": hk_trade_date,
            "us_trade_date": us_trade_date,
            "report_rel_path": relative_to_project(report_path),
            "publish_queue_rel_path": publish_rel_path,
            "source_latest_report_rel_path": snapshot_payload.get("latest_report_rel_path"),
        },
    )
    return report_path, publish_rel_path, entry


def main():
    parser = argparse.ArgumentParser(description="Materialize a formal daily report from the latest candidate")
    parser.add_argument("--date", help="Target daily report date; defaults to latest daily_reporting_snapshot entity_id")
    parser.add_argument("--enqueue-publish", action="store_true", help="Also copy the formal report into 07_publish/queue")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    report_date = args.date or latest_available_report_date(conn)
    report_path, publish_rel_path, entry = materialize_report(conn, report_date, enqueue_publish=args.enqueue_publish)
    conn.commit()
    conn.close()

    log_run(
        "materialize_daily_report.py",
        "success",
        "formal daily report materialized",
        {
            "entity_id": report_date,
            "report_rel_path": relative_to_project(report_path),
            "publish_queue_rel_path": publish_rel_path,
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Formal daily report: {report_path}")
    if publish_rel_path:
        print(f"Publish queue copy: {publish_rel_path}")


if __name__ == "__main__":
    main()
