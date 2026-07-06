#!/usr/bin/env python3
"""Serve the SMR business-facing dashboard locally."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import webbrowser
from datetime import date as dt_date
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_dashboard import DB_PATH, build_dashboard_state, resolve_project_path
from smr_decision import ensure_decision_tables, review_recommendation
from today_overview_view_model import build_today_overview_view_model
from signal_flow_view_model import build_signal_flow_view_model
from research_queue_view_model import build_research_queue_view_model
from coverage_pool_view_model import build_coverage_pool_view_model
from data_health_view_model import build_data_health_view_model


NAV_ITEMS = [
    ("/", "今日总览"),
    ("/coverage", "覆盖池"),
    ("/signals", "信号流"),
    ("/research", "研究队列"),
    ("/health", "数据健康"),
]

OPERATIONS_BLUEPRINT = [
    {
        "job_id": "deep_market_scan",
        "label": "深度市场扫描",
        "time_text": "清晨 + 午后",
        "frequency_text": "通常每天 2 次",
        "purpose_text": "抓公开卖方信号并刷新 AI、光通信、新能源、scale up、scale out 的主题分析结果。",
        "deliverable_text": "更新机会挖掘页、主题雷达和深度市场分析快照。",
        "schedule_note": "按外部调度实跑，近期日志显示通常双次运行。",
        "formal_schedule": False,
    },
    {
        "job_id": "morning_us",
        "label": "晨间美股链",
        "time_text": "06:00",
        "frequency_text": "工作日 1 次",
        "purpose_text": "同步美股隔夜行情、业绩监控和美股联动因子，必要时刷新动态池。",
        "deliverable_text": "更新美股联动因子、动态池、个股分析基底。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "preopen_report",
        "label": "盘前简报链",
        "time_text": "09:00",
        "frequency_text": "工作日 1 次",
        "purpose_text": "刷新资金异动、价格区间推演、日报快照和正式盘前简报。",
        "deliverable_text": "更新日报页、个股分析摘要和 dispatch 候选。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "afternoon_close",
        "label": "午后收盘链",
        "time_text": "15:30",
        "frequency_text": "工作日 1 次",
        "purpose_text": "刷新 A/H 行情、因子、研究观察、动态池、价格区间推演和轮动候选。",
        "deliverable_text": "更新研究页、调仓动作页和个股分析页。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "afternoon_refresh",
        "label": "午后二次刷新",
        "time_text": "16:30",
        "frequency_text": "工作日 1 次",
        "purpose_text": "补跑因子和研究候选，重新收口轮动、动作和区间推演。",
        "deliverable_text": "更新研究页、调仓动作页和第二版个股分析结果。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "opportunity_radar",
        "label": "主动机会雷达链",
        "time_text": "17:10",
        "frequency_text": "工作日 1 次",
        "purpose_text": "把异动、因子、研究池、轻量回测、攻防推演、生命周期和纸面复盘收敛成机会闭环。",
        "deliverable_text": "更新机会雷达、策略证据、攻防推演、生命周期、纸面观察单和纸面表现复盘。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "portfolio_review",
        "label": "持仓复盘",
        "time_text": "19:30",
        "frequency_text": "工作日 1 次",
        "purpose_text": "更新持仓盈亏并生成组合复核结论。",
        "deliverable_text": "更新持仓复盘结果，供风险和动作链继续使用。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "daily_report",
        "label": "晚间日报链",
        "time_text": "20:30",
        "frequency_text": "工作日 1 次",
        "purpose_text": "物化正式日报，并同步 dispatch 候选。",
        "deliverable_text": "更新日报页、调度面板和候选版沉淀。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "risk_review",
        "label": "晚间风控链",
        "time_text": "21:00",
        "frequency_text": "工作日 1 次",
        "purpose_text": "刷新风险快照和买卖风控结论。",
        "deliverable_text": "更新风险结果页和买卖决策建议。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
    {
        "job_id": "next_day_plan",
        "label": "次日计划链",
        "time_text": "22:00",
        "frequency_text": "工作日 1 次",
        "purpose_text": "抽取未来催化并刷新次日 dispatch 收口。",
        "deliverable_text": "更新事件页、调度面板和次日计划。",
        "schedule_note": "正式定时主链。",
        "formal_schedule": True,
    },
]

CODE_LABELS = {
    "reference_only": "参照层建议",
    "recommended": "推荐池",
    "Recommended": "推荐池",
    "candidate": "候选池",
    "Candidate": "候选池",
    "watchlist": "观察池",
    "Watchlist": "观察池",
    "portfolio_seed": "持仓参照层",
    "seed": "种子池",
    "us_benchmark": "美股对照池",
    "swap_ready": "优先换仓",
    "swap_watch": "观察换仓",
    "swap_blocked": "阻塞换仓",
    "holding_watch": "持仓复核",
    "opportunity_followup": "机会跟踪",
    "high_conviction_watch": "高优先观察",
    "breakout_with_volume": "放量突破",
    "trend_continuation": "趋势延续",
    "price_volume_acceleration": "价量加速",
    "overheat_watch": "短线过热",
    "reversal_probe": "反转试探",
    "watch_only": "仅观察",
    "paper_watch_candidate": "纸面观察候选",
    "paper_watch_ready": "纸面观察就绪",
    "breakout_20d_volume_hold10": "20日放量突破后持有10日",
    "ma20_ma60_trend_hold20": "20/60日均线多头排列后持有20日",
    "pullback_above_ma60_hold10": "60日线上方回撤后持有10日",
    "new_candidate": "新进雷达",
    "promoted": "晋级",
    "strengthening": "强化",
    "persistent_watch": "持续观察",
    "cooling": "降温",
    "demoted": "降级",
    "dropped_from_radar": "退出雷达",
    "watch_with_evidence": "带证据观察",
    "research_first": "先补研究",
    "monitor_only": "仅监控",
    "radar_candidate": "雷达候选",
    "paper_watch_active": "纸面观察中",
    "awaiting_market_data": "等待新行情",
    "trigger_confirmed": "纸面触发成立",
    "invalidated": "纸面失效",
    "working": "观察运行中",
    "positive_validation": "正向验证",
    "failed_validation": "验证失败",
    "pending": "待验证",
    "ready_for_paper_watch": "纸面证据通过",
    "thin_sample": "样本偏薄",
    "mixed_evidence": "混合证据",
    "negative_evidence": "负证据",
    "high": "高",
    "medium": "中",
    "low": "低",
    "trend_follow": "趋势跟随",
    "trend_positive": "趋势偏正",
    "trend_strong": "趋势强",
    "trend_hot": "短线偏热",
    "under_ma60": "60日线下方",
    "observe": "观察",
    "repair_needed": "等待修复",
    "watch_only": "仅观察",
    "ready": "可推进",
    "buy": "可买入",
    "buy_small": "小仓试单",
    "watch": "继续观察",
    "block": "暂不买入",
    "sell": "优先卖出",
    "trim": "建议减仓",
    "hold": "继续持有",
    "normal": "正常推进",
    "cautious": "谨慎推进",
    "blocked": "阻塞",
    "none": "未分层",
    "warning": "关注",
    "critical": "高风险",
    "risk_alert": "风险提醒",
    "same_sector_upgrade": "同主线做强换弱",
    "cross_sector_mainline_switch": "跨主题切主线",
    "cross_sector_probe": "跨主题试探",
    "semiconductor_photonics": "光通信",
    "semiconductor_compute": "算力链",
    "ai_agent": "AI Agent",
    "embodied_ai": "具身智能",
    "ai": "人工智能",
    "photonics": "光通信",
    "new_energy": "新能源",
    "scale_up": "Scale Up",
    "scale_out": "Scale Out",
    "news": "资讯",
    "research": "研报",
    "announcement": "公告",
    "fresh": "较新",
    "warn": "预警",
    "fresh_hot": "很新",
    "usable": "还能参考",
    "aging": "开始变旧",
    "stale": "偏旧",
    "daily": "日频",
    "quarterly": "季频",
    "missing": "缺失",
    "unknown": "未知",
    "data_first": "先补数据",
    "evidence_first": "先补证据",
    "review_triggers": "复核触发",
    "normal_watch": "正常观察",
    "event_backed": "有新证据",
    "stale_evidence": "证据偏旧",
    "price_only": "仅价格信号",
    "overheated_without_fresh_evidence": "偏热缺新证据",
    "success": "成功",
    "failed": "失败",
    "error": "错误",
    "initial": "首次试单",
    "initial_build": "首次试单",
    "initial_action": "首次试单",
    "add": "加仓条件",
    "add_position": "加仓条件",
    "reduce": "降敞口条件",
    "reduce_exposure": "降敞口条件",
    "reduce_position": "减仓条件",
    "exit": "退出条件",
    "exit_observation": "退出观察",
    "stop_loss": "止损条件",
    "hold": "继续持有条件",
    "watch": "继续观察",
    "dry_run": "演练",
    "running": "运行中",
    "partial": "部分成功",
    "skipped": "跳过",
    "SSE": "上交所",
    "SZSE": "深交所",
    "northbound": "北向",
    "southbound": "南向",
    "northbound_sh": "沪股通",
    "southbound_sh": "港股通(沪)",
    "northbound_sz": "深股通",
    "southbound_sz": "港股通(深)",
    "announcement_general": "一般公告",
    "monthly_return": "月度股本变动",
    "annual_results_announcement": "年报业绩公告",
    "interim_results_announcement": "中报 / 中期业绩",
    "board_meeting_notice": "董事会通知",
    "investor_relations_activity": "投资者关系活动记录",
    "investor_presentation": "演示稿",
    "earnings_call_material": "电话会 / 业绩会材料",
    "earnings_release": "业绩稿 / 业绩披露",
    "quarterly_report": "季报",
    "research_structured": "结构化研报",
    "research_table_structured": "结构化研报表",
    "research_pdf_text": "研报PDF文本",
    "research_search": "研报搜索快照",
    "research_article": "研报正文",
    "research_pdf": "研报PDF",
    "news_search": "资讯搜索快照",
    "public_analyst_signal": "公开卖方参照",
    "public_transcript": "公开电话会文字稿",
    "public_transcript_fool": "公开电话会文字稿",
    "official_ir_material": "公司 IR 官网",
    "sec_filing_document": "SEC 主文件",
    "sec_earnings_material": "SEC 业绩附件",
    "cninfo_announcement": "巨潮资讯",
    "hkex_announcement": "港交所披露",
    "ir_material_page": "投关材料页面",
    "ir_material_pdf": "投关材料PDF",
    "ir_landing_page": "投关主页",
    "sec_earnings_material": "SEC业绩材料",
    "sec_filing_document": "SEC文件正文",
    "sec_submissions_json": "SEC提交清单",
    "analyst_report": "研报正文",
    "analyst_report_table": "研报表格",
    "analyst_report_structured": "研报PDF文本",
    "news_digest_item": "资讯搜索快照",
    "news_article": "资讯正文",
    "analyst_signal_summary": "公开卖方摘要",
    "supportive_strong": "卖方强支撑",
    "supportive": "卖方支撑",
    "neutral": "中性",
    "neutral_watch": "卖方中性偏跟踪",
    "stretched": "卖方提示偏透支",
    "cautious": "卖方偏谨慎",
    "not_applicable": "不适用",
    "marketscreener": "MarketScreener",
    "fool": "The Motley Fool",
    "repair_below_ma20": "20日线下修复",
    "neutral_observe": "中性观察",
    "ma20_above_ma60": "20日线位于60日线上方",
    "ma20_below_ma60": "20日线仍在60日线下",
    "earnings_pressure": "盈利承压",
    "earnings_growth": "盈利增长",
    "revenue_growth": "营收增长",
    "revenue_pressure": "营收承压",
    "rich_valuation": "高估值压力",
    "short_term_hot": "短线过热",
    "research_stale": "研究偏旧",
    "target_gap_positive": "目标空间尚可",
    "target_gap_thin": "目标空间偏薄",
    "high_conviction": "高潜在低估",
    "medium_conviction": "继续深挖",
    "strong": "值得重点深挖",
    "active": "继续跟踪",
    "missing_price_window": "缺少价格数据",
}

INLINE_TOKEN_RE = re.compile(r"(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
UNORDERED_LIST_RE = re.compile(r"^[-*+]\s+(.*)$")
ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(.*)$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
REPORT_HEADER_LINE_RE = re.compile(r"\*\*撰写时间\*\*：[^\n]+")
REPORT_CAPITAL_LINE_RE = re.compile(
    r"\*\*资金流(?:事实|随时)\*\*：两融\s+(?P<margin>[^|]+?)\s*\|\s*互联互通日频\s+(?P<stock>[^|]+?)\s*\|\s*互联互通持股按官方可得频率分别展示"
)
LIVE_COPY_REPLACEMENTS = [
    ("官方事实日期", "官方随时日期"),
    ("官方事实日", "官方随时日期"),
    ("最新事实日期", "最新随时日期"),
    ("最新事实日", "最新随时日期"),
    ("事实日期", "随时日期"),
    ("事实日", "随时"),
    ("事实口径", "随时口径"),
    ("事实展示", "随时展示"),
]


def plain_text(value: str | None) -> str:
    if value in (None, ""):
        return ""
    text = str(value)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"#+\s*", "", text)
    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def relabel_live_copy(value: str | None) -> str:
    if value in (None, ""):
        return ""
    text = str(value)
    for source, target in LIVE_COPY_REPLACEMENTS:
        text = text.replace(source, target)
    return text


def compact_text(value: str | None, limit: int = 86) -> str:
    text = plain_text(value)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def code_label(value: str | None) -> str:
    if value in (None, ""):
        return "-"
    return CODE_LABELS.get(str(value), plain_text(str(value)))


def business_text(value: str | None, limit: int | None = None) -> str:
    text = plain_text(value)
    if not text:
        return ""
    for token, label in CODE_LABELS.items():
        text = re.sub(rf"\b{re.escape(token)}\b", label, text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit is not None and len(text) > limit:
        return f"{text[: limit - 1].rstrip()}…"
    return text


def live_business_text(value: str | None, limit: int | None = None) -> str:
    return business_text(relabel_live_copy(value), limit=limit)


def current_report_market_line(overview: dict, generated_at: str | None) -> str:
    a_expected = overview.get("a_share_expected_trade_date") or overview.get("a_share_trade_date") or "-"
    hk_expected = overview.get("hk_expected_trade_date") or overview.get("hk_trade_date") or "-"
    us_expected = overview.get("us_expected_trade_date") or overview.get("us_trade_date") or "-"
    written_at = str(generated_at or "").strip()
    written_time = written_at[11:16] if len(written_at) >= 16 else "--:--"
    return (
        f"**撰写时间**：{written_time} 上海 | "
        f"**A股实时锚点**：{a_expected} | "
        f"**港股实时锚点**：{hk_expected} | "
        f"**美股实时锚点**：{us_expected}"
    )


def current_report_capital_line(capital: dict) -> str:
    margin = (capital.get("margin_balance") or {}).get("anchor_trade_date") or "-"
    stock_connect = (capital.get("stock_connect") or {}).get("anchor_trade_date") or "-"
    return (
        f"**资金流随时**：两融 {margin} | "
        f"互联互通日频 {stock_connect} | "
        "互联互通持股按官方可得频率分别展示"
    )


def rewrite_report_live_header(text: str | None, overview: dict, capital: dict, generated_at: str | None) -> str:
    if text in (None, ""):
        return ""
    live_market_line = current_report_market_line(overview, generated_at)
    live_capital_line = current_report_capital_line(capital)
    updated = REPORT_HEADER_LINE_RE.sub(live_market_line, str(text), count=1)
    updated = REPORT_CAPITAL_LINE_RE.sub(live_capital_line, updated, count=1)
    return relabel_live_copy(updated)


def stock_connect_estimate_reason_text(reason: str | None) -> str:
    mapping = {
        "probe_trade_date_mismatch": "实时试探日期和官方随时日期不一致，未回填",
        "probe_missing_total_amount": "实时探针没给成交额，未回填",
        "probe_missing_net_buy_amount": "实时探针没给净买额，未回填",
        "probe_missing": "本轮没有拿到实时探针",
    }
    return mapping.get(str(reason or "").strip(), "当前未回填")


def stock_connect_basis_text(item: dict) -> str:
    if item.get("buy_sell_estimated"):
        return "官方+估算"
    if item.get("direction") == "northbound":
        return "官方（买卖拆分未回填）"
    return "官方"


def badge(text: str | None, tone: str = "neutral") -> str:
    if text in (None, ""):
        text = "-"
    return f"<span class='badge {escape(tone)}'>{escape(code_label(str(text)))}</span>"


def fmt_pct(value: float | None) -> str:
    if value in (None, ""):
        return "-"
    return f"{value:+.2f}%"


def fmt_number(value: float | int | None) -> str:
    if value in (None, ""):
        return "-"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def fmt_ratio(value: float | None) -> str:
    if value in (None, ""):
        return "-"
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return str(value)


def fmt_lag_days(value: int | str | None) -> str:
    if value in (None, ""):
        return "未知"
    try:
        days = int(value)
    except (TypeError, ValueError):
        return str(value)
    if days <= 0:
        return "已同步"
    return f"延迟 {days} 天"


def fmt_event_recency(published_at: str | None, today: str | None = None) -> str:
    published_text = str(published_at or "").strip()
    if not published_text:
        return "事件日期未知"
    published_date = published_text[:10]
    try:
        published_dt = dt_date.fromisoformat(published_date)
    except ValueError:
        return published_text
    try:
        today_dt = dt_date.fromisoformat(str(today or dt_date.today().isoformat())[:10])
    except ValueError:
        today_dt = dt_date.today()
    days = max((today_dt - published_dt).days, 0)
    if days <= 3:
        label = "较新"
    elif days <= 10:
        label = "开始变旧"
    else:
        label = "偏旧"
    return f"{published_date} · {label}（{days} 天前）"


def status_tone(value: str | None) -> str:
    key = str(value or "").strip().lower()
    if key in {
        "success",
        "generated",
        "recorded",
        "clear",
        "captured",
        "compiled",
        "normalized",
        "synced",
        "ready",
        "buy",
        "hold",
        "fresh",
        "fresh_hot",
        "strong",
        "active",
        "high_conviction",
        "high_conviction_watch",
        "paper_watch_candidate",
        "paper_watch_ready",
        "watch_with_evidence",
        "ready_for_paper_watch",
        "paper_watch_active",
        "new_candidate",
        "promoted",
        "strengthening",
        "trigger_confirmed",
        "positive_validation",
        "event_backed",
        "normal_watch",
        "review_triggers",
    }:
        return "good"
    if key in {
        "failed",
        "error",
        "blocked",
        "critical",
        "warning",
        "cautious",
        "sell",
        "trim",
        "buy_small",
        "medium_conviction",
        "research_first",
        "thin_sample",
        "mixed_evidence",
        "negative_evidence",
        "cooling",
        "demoted",
        "dropped_from_radar",
        "invalidated",
        "failed_validation",
        "warn",
        "data_first",
        "evidence_first",
        "stale_evidence",
        "price_only",
        "overheated_without_fresh_evidence",
    }:
        return "warning"
    if key in {
        "dry_run",
        "watch_only",
        "monitor_only",
        "observe",
        "neutral",
        "unknown",
        "missing",
        "radar_candidate",
        "persistent_watch",
        "awaiting_market_data",
        "working",
        "pending",
    }:
        return "ghost"
    return "neutral"


def render_count_badges(counts: dict[str, int] | None, empty_text: str = "暂无记录") -> str:
    if not counts:
        return f"<span class='muted'>{escape(empty_text)}</span>"
    return "<div class='badge-row'>" + "".join(
        badge(f"{code_label(key)} {fmt_number(value)}", status_tone(key)) for key, value in counts.items()
    ) + "</div>"


def public_signal_label(item: dict) -> str | None:
    return item.get("public_analyst_label") or item.get("stance_label")


def public_signal_summary(item: dict) -> str:
    if public_signal_label(item) == "not_applicable":
        return "当前市场暂不适用这条公开卖方参照链路。"
    summary = item.get("public_analyst_summary") or item.get("summary")
    if summary:
        return business_text(summary)
    mean_consensus = item.get("public_analyst_mean_consensus") or item.get("mean_consensus")
    spread = item.get("public_analyst_spread_avg_target_pct")
    if spread in (None, ""):
        spread = item.get("spread_avg_target_pct")
    analysts_count = item.get("public_analyst_analysts_count") or item.get("analysts_count")
    parts = []
    if mean_consensus:
        parts.append(f"一致预期 {mean_consensus}")
    if analysts_count:
        parts.append(f"覆盖 {analysts_count} 家")
    if spread not in (None, ""):
        parts.append(f"平均目标空间 {fmt_pct(spread)}")
    return " / ".join(parts) if parts else "当前没有公开卖方参照。"


def public_signal_source_rel_path(item: dict) -> str | None:
    return item.get("public_analyst_source_rel_path") or item.get("source_rel_path")


def public_transcript_source_rel_path(item: dict) -> str | None:
    return item.get("public_transcript_source_rel_path") or item.get("source_rel_path")


def official_material_freshness(item: dict) -> str | None:
    return item.get("official_material_freshness") or item.get("freshness_label")


def official_material_summary(item: dict) -> str:
    summary = item.get("official_material_summary") or item.get("summary")
    if summary:
        return business_text(summary)
    latest_event_type = item.get("official_material_latest_event_type") or item.get("latest_event_type")
    latest_publish_time = item.get("official_material_latest_publish_time") or item.get("latest_publish_time")
    latest_title = item.get("official_material_latest_title") or item.get("latest_title")
    parts = []
    if latest_event_type:
        parts.append(code_label(latest_event_type))
    if latest_publish_time:
        parts.append(latest_publish_time)
    if latest_title:
        parts.append(compact_text(latest_title, 72))
    return " / ".join(parts) if parts else "当前没有可直接复核的高价值官方一手材料。"


def official_material_source_rel_paths(item: dict) -> list[str]:
    return (item.get("official_material_source_rel_paths") or item.get("source_rel_paths") or [])[:]


def official_material_latest_title(item: dict) -> str | None:
    return item.get("official_material_latest_title") or item.get("latest_title")


def official_material_latest_event_type(item: dict) -> str | None:
    return item.get("official_material_latest_event_type") or item.get("latest_event_type")


def official_material_latest_publish_time(item: dict) -> str | None:
    return item.get("official_material_latest_publish_time") or item.get("latest_publish_time")


def external_research_summary(item: dict) -> str:
    parts = []
    source_kind = item.get("external_research_kind") or item.get("source_kind")
    org_name = item.get("external_research_org") or item.get("org_name")
    rating_name = item.get("external_research_rating") or item.get("rating_name")
    published_at = item.get("external_research_published_at") or item.get("published_at")
    title = item.get("title")
    if source_kind:
        parts.append(code_label(source_kind))
    if org_name:
        parts.append(org_name)
    if rating_name:
        parts.append(rating_name)
    if published_at:
        parts.append(published_at)
    if not parts and title:
        parts.append(compact_text(title, 88))
    return " / ".join(parts) if parts else "当前没有可直接复核的外部研究锚点。"


def public_transcript_summary(item: dict) -> str:
    summary = item.get("public_transcript_summary") or item.get("summary")
    if summary:
        return business_text(summary)
    parts = []
    provider = item.get("public_transcript_provider") or item.get("provider")
    quarter_label = item.get("public_transcript_quarter_label") or item.get("quarter_label")
    published_at = item.get("public_transcript_published_at") or item.get("published_at")
    speaker_count = item.get("public_transcript_speaker_count") or item.get("speaker_count")
    speakers = item.get("speakers") or []
    if provider:
        parts.append(code_label(provider))
    if quarter_label:
        parts.append(f"覆盖 {quarter_label} 业绩会")
    if published_at:
        parts.append(f"发布时间 {published_at[:10]}")
    if speaker_count not in (None, ""):
        parts.append(f"识别到约 {speaker_count} 位发言人")
    if speakers:
        parts.append(f"前几位包括 {', '.join(speakers[:3])}")
    return " / ".join(parts) if parts else "当前没有可直接复核的公开电话会文字稿。"


def transcript_status_code(item: dict | None) -> str:
    if not item:
        return "missing"
    return str(item.get("freshness_label") or item.get("public_transcript_freshness") or "missing").strip().lower() or "missing"


def transcript_status_sentence(item: dict | None, limit: int = 96) -> str:
    snapshot = item or {}
    status = transcript_status_code(snapshot)
    if status == "fresh":
        lead = "有较新的管理层原话，可直接复核最近一次表述。"
    elif status == "usable":
        lead = "有还能参考的管理层原话，但临近新事件时仍要补更新版本。"
    elif status == "stale":
        lead = "现有管理层原话偏旧，只能当背景资料。"
    else:
        return "当前没有可直接复核的管理层原话。"
    summary = public_transcript_summary(snapshot)
    if summary and summary != "当前没有可直接复核的公开电话会文字稿。":
        return f"{lead} {compact_text(summary, limit)}"
    return lead


def render_research_subject(name: str, ts_code: str | None, detail_enabled_codes: set[str] | None = None) -> str:
    if ts_code and (detail_enabled_codes is None or ts_code in detail_enabled_codes):
        return f"<a href='{research_detail_href(ts_code)}'>{escape(name)}</a>"
    return escape(name)


def render_public_signal_panel(
    items: list[dict], title: str, intro: str, empty_text: str, detail_enabled_codes: set[str] | None = None
) -> str:
    if not items:
        return (
            "<article class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='section-intro'>{escape(intro)}</div>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</article>"
        )
    cards = []
    for item in items:
        ts_code = item.get("ts_code")
        name = item.get("name") or ts_code or "-"
        source_rel_path = public_signal_source_rel_path(item)
        source_html = link_for_rel_path(source_rel_path, "查看公开卖方原文") if source_rel_path else "暂无原文"
        badges = render_badge_group(
            [
                (public_signal_label(item), "neutral"),
                (item.get("public_analyst_mean_consensus") or item.get("mean_consensus"), "ghost"),
                (item.get("public_analyst_freshness") or item.get("freshness_label"), "ghost"),
            ]
        )
        detail_link = render_research_subject(name, ts_code, detail_enabled_codes)
        cards.append(
            "<article class='story-card'>"
            "<div class='story-meta'>"
            f"{badges}"
            f"<span class='muted'>{escape(item.get('public_analyst_published_at') or item.get('published_at') or '-')}</span>"
            "</div>"
            f"<h3 class='story-title'>{detail_link}</h3>"
            f"<div class='muted'>{escape(ts_code or '-')}</div>"
            f"<p style='margin:10px 0 8px 0'>{escape(public_signal_summary(item))}</p>"
            f"<div class='story-footer'>{source_html}</div>"
            "</article>"
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{''.join(cards)}"
        "</article>"
    )


def render_public_transcript_panel(
    items: list[dict], title: str, intro: str, empty_text: str, detail_enabled_codes: set[str] | None = None
) -> str:
    if not items:
        return (
            "<article class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='section-intro'>{escape(intro)}</div>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</article>"
        )
    cards = []
    for item in items:
        ts_code = item.get("ts_code")
        name = item.get("name") or ts_code or "-"
        source_rel_path = public_transcript_source_rel_path(item)
        source_html = link_for_rel_path(source_rel_path, "查看电话会文字稿") if source_rel_path else "暂无原文"
        badges = render_badge_group(
            [
                (item.get("public_transcript_freshness") or item.get("freshness_label"), "neutral"),
                (item.get("public_transcript_quarter_label") or item.get("quarter_label"), "ghost"),
                (item.get("public_transcript_speaker_count") or item.get("speaker_count"), "ghost"),
            ]
        )
        detail_link = render_research_subject(name, ts_code, detail_enabled_codes)
        speakers = ", ".join((item.get("speakers") or [])[:4])
        cards.append(
            "<article class='story-card'>"
            "<div class='story-meta'>"
            f"{badges}"
            f"<span class='muted'>{escape(item.get('public_transcript_published_at') or item.get('published_at') or '-')}</span>"
            "</div>"
            f"<h3 class='story-title'>{detail_link}</h3>"
            f"<div class='muted'>{escape(ts_code or '-')}</div>"
            f"<p style='margin:10px 0 8px 0'>{escape(public_transcript_summary(item))}</p>"
            f"<div class='muted' style='margin-bottom:8px'>{escape(speakers if speakers else '当前没有提取到发言人名单')}</div>"
            f"<div class='story-footer'>{source_html}</div>"
            "</article>"
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{''.join(cards)}"
        "</article>"
    )


def render_official_material_panel(
    items: list[dict], title: str, intro: str, empty_text: str, detail_enabled_codes: set[str] | None = None
) -> str:
    if not items:
        return (
            "<article class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='section-intro'>{escape(intro)}</div>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</article>"
        )
    cards = []
    for item in items:
        ts_code = item.get("ts_code")
        name = item.get("name") or ts_code or "-"
        source_paths = official_material_source_rel_paths(item)
        source_html = link_for_rel_path(source_paths[0], "查看官方原文") if source_paths else "暂无原文"
        latest_title = official_material_latest_title(item)
        latest_event_type = official_material_latest_event_type(item)
        badges = render_badge_group(
            [
                (official_material_freshness(item), "neutral"),
                (latest_event_type, "ghost"),
                (item.get("item_count"), "ghost"),
            ]
        )
        detail_link = render_research_subject(name, ts_code, detail_enabled_codes)
        cards.append(
            "<article class='story-card'>"
            "<div class='story-meta'>"
            f"{badges}"
            f"<span class='muted'>{escape(official_material_latest_publish_time(item) or '-')}</span>"
            "</div>"
            f"<h3 class='story-title'>{detail_link}</h3>"
            f"<div class='muted'>{escape(ts_code or '-')}</div>"
            f"<p style='margin:10px 0 8px 0'>{escape(official_material_summary(item))}</p>"
            f"<div class='muted' style='margin-bottom:8px'>{escape(compact_text(latest_title, 88) if latest_title else '暂无标题锚点')}</div>"
            f"<div class='story-footer'>{source_html}</div>"
            "</article>"
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{''.join(cards)}"
        "</article>"
    )


def render_external_research_panel(
    items: list[dict], title: str, intro: str, empty_text: str, detail_enabled_codes: set[str] | None = None
) -> str:
    if not items:
        return (
            "<article class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='section-intro'>{escape(intro)}</div>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</article>"
        )
    cards = []
    for item in items:
        ts_code = item.get("ts_code")
        name = item.get("name") or ts_code or "-"
        source_rel_path = item.get("source_rel_path")
        source_html = link_for_rel_path(source_rel_path, "查看外部研报") if source_rel_path else "暂无原文"
        badges = render_badge_group(
            [
                (item.get("source_kind"), "neutral"),
                (item.get("rating_name"), "ghost"),
                (item.get("org_name"), "ghost"),
            ]
        )
        detail_link = render_research_subject(name, ts_code, detail_enabled_codes)
        cards.append(
            "<article class='story-card'>"
            "<div class='story-meta'>"
            f"{badges}"
            f"<span class='muted'>{escape(item.get('published_at') or '-')}</span>"
            "</div>"
            f"<h3 class='story-title'>{detail_link}</h3>"
            f"<div class='muted'>{escape(ts_code or '-')}</div>"
            f"<p style='margin:10px 0 8px 0'>{escape(external_research_summary(item))}</p>"
            f"<div class='muted' style='margin-bottom:8px'>{escape(compact_text(item.get('title'), 88) if item.get('title') else '暂无标题锚点')}</div>"
            f"<div class='story-footer'>{source_html}</div>"
            "</article>"
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{''.join(cards)}"
        "</article>"
    )


def link_for_artifact(artifact: dict | None) -> str:
    if not artifact:
        return "<span class='muted'>暂无原文</span>"
    rel_path = artifact.get("rel_path")
    if not rel_path:
        return "<span class='muted'>暂无原文</span>"
    href = f"/artifact?path={quote(rel_path)}"
    label = artifact.get("label") or rel_path
    return f"<a href='{href}'>{escape(label)}</a><span class='muted'> · {escape(rel_path)}</span>"


def research_detail_href(ts_code: str | None) -> str:
    return f"/research/item?ts_code={quote(ts_code or '')}"


def action_detail_href(action_id: str | None) -> str:
    return f"/portfolio/action?id={quote(action_id or '')}"


def render_nav(current_path: str) -> str:
    items = []
    for href, label in NAV_ITEMS:
        cls = "nav-link active" if href == current_path else "nav-link"
        items.append(f"<a class='{cls}' href='{href}'>{escape(label)}</a>")
    return "".join(items)


def render_shell(
    *,
    page_title: str,
    current_path: str,
    hero_title: str,
    hero_subtitle: str,
    body: str,
    refresh_seconds: int,
    hero_facts: list[tuple[str, str | int | float | None]] | None = None,
    snapshot_generated_at: str | None = None,
    state_version: str | None = None,
    show_status_strip: bool = True,
) -> str:
    facts_html = ""
    if hero_facts:
        facts_html = "<div class='hero-facts'>" + render_kv_chips(hero_facts, chip_class="hero-chip") + "</div>"
    refresh_meta = ""
    if refresh_seconds > 0 and not state_version:
        refresh_meta = f'  <meta http-equiv="refresh" content="{refresh_seconds}">\n'
    status_strip_html = ""
    if show_status_strip and (snapshot_generated_at or state_version):
        status_strip_html = (
            "<section class='status-strip'>"
            "<div class='status-pill'><span>自动更新</span><strong data-auto-refresh-state>已开启</strong></div>"
            f"<div class='status-pill'><span>当前快照</span><strong data-auto-refresh-snapshot>{escape(snapshot_generated_at or '-')}</strong></div>"
            f"<div class='status-pill'><span>检查间隔</span><strong>{refresh_seconds} 秒</strong></div>"
            "<div class='status-pill'><span>最近检查</span><strong data-auto-refresh-check>尚未检查</strong></div>"
            "</section>"
        )
    auto_refresh_script = ""
    if state_version:
        refresh_config = json.dumps(
            {
                "stateVersion": state_version,
                "refreshMs": max(refresh_seconds, 10) * 1000,
            },
            ensure_ascii=False,
        )
        auto_refresh_script = f"""
  <script>
    (() => {{
      const config = {refresh_config};
      let seenVersion = config.stateVersion;
      const stateLabel = document.querySelector("[data-auto-refresh-state]");
      const snapshotLabel = document.querySelector("[data-auto-refresh-snapshot]");
      const checkLabel = document.querySelector("[data-auto-refresh-check]");
      const setText = (node, value) => {{
        if (node) node.textContent = value;
      }};
      const nowText = () => new Date().toLocaleString("zh-CN", {{ hour12: false }});
      const hardRefresh = () => {{
        const url = new URL(window.location.href);
        url.searchParams.set("_ts", String(Date.now()));
        window.location.replace(url.toString());
      }};
      async function checkState() {{
        setText(checkLabel, nowText());
        setText(stateLabel, "检查中");
        try {{
          const response = await fetch("/api/state?ts=" + Date.now(), {{ cache: "no-store" }});
          if (!response.ok) {{
            throw new Error("HTTP " + response.status);
          }}
          const payload = await response.json();
          if (payload.generated_at) {{
            setText(snapshotLabel, payload.generated_at);
          }}
          if (payload.state_version && payload.state_version !== seenVersion) {{
            setText(stateLabel, "检测到新结果，正在刷新");
            seenVersion = payload.state_version;
            window.setTimeout(hardRefresh, 150);
            return;
          }}
          setText(stateLabel, "已开启");
        }} catch (error) {{
          setText(stateLabel, "检查失败");
        }}
      }}
      window.setTimeout(checkState, 5000);
      window.setInterval(checkState, config.refreshMs);
    }})();
  </script>"""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
{refresh_meta}  <title>{escape(page_title)}</title>
  <style>
    :root {{
      --bg: #eef2f5;
      --panel: rgba(255, 255, 255, 0.92);
      --ink: #1f272e;
      --muted: #6d7579;
      --line: rgba(31, 39, 46, 0.1);
      --brand: #155a6f;
      --brand-soft: rgba(21, 90, 111, 0.08);
      --good: #165f4f;
      --warn: #9a5b14;
      --ghost: #546673;
      --shadow: 0 20px 48px rgba(31, 39, 46, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: linear-gradient(180deg, #f9fbfc 0%, var(--bg) 100%);
      font-family: "PingFang SC", "Noto Serif SC", "Hiragino Sans GB", "Source Han Serif SC", Georgia, serif;
      line-height: 1.58;
    }}
    a {{
      color: var(--brand);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    code, pre {{
      font-family: "SFMono-Regular", "JetBrains Mono", Menlo, monospace;
    }}
    pre {{
      margin: 0.75rem 0 0;
      padding: 1rem;
      border-radius: 18px;
      white-space: pre-wrap;
      overflow-x: auto;
      border: 1px solid rgba(31, 39, 46, 0.08);
      background: rgba(31, 39, 46, 0.045);
      font-size: 12px;
      line-height: 1.48;
    }}
    .page {{
      max-width: 1380px;
      margin: 0 auto;
      padding: 26px 18px 72px;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}
    .brand {{
      font-size: 14px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    .nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .nav-link {{
      padding: 0.5rem 0.95rem;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.68);
      color: var(--ink);
      font-size: 13px;
    }}
    .nav-link.active {{
      background: var(--brand);
      color: white;
      border-color: var(--brand);
    }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 26px 26px 22px;
      margin-bottom: 18px;
    }}
    .hero h1 {{
      margin: 0 0 10px;
      font-size: clamp(34px, 5vw, 56px);
      line-height: 1.04;
      letter-spacing: -0.04em;
    }}
    .hero p {{
      margin: 0;
      max-width: 880px;
      color: var(--muted);
      font-size: 16px;
    }}
    .hero-facts {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}
    .hero-chip {{
      display: inline-flex;
      align-items: baseline;
      gap: 7px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(21, 90, 111, 0.08);
      border: 1px solid rgba(21, 90, 111, 0.12);
      font-size: 13px;
    }}
    .hero-chip span {{
      color: var(--muted);
    }}
    .hero-chip strong {{
      color: var(--ink);
      font-size: 13px;
    }}
    .status-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 8px;
      margin-bottom: 14px;
    }}
    .status-pill {{
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.76);
      box-shadow: 0 8px 18px rgba(31, 39, 46, 0.04);
    }}
    .status-pill span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .status-pill strong {{
      display: block;
      font-size: 15px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 22px;
      margin-bottom: 18px;
    }}
    .panel h2 {{
      margin: 0 0 12px;
      font-size: 24px;
      letter-spacing: -0.02em;
    }}
    .panel h3 {{
      margin: 0 0 8px;
      font-size: 18px;
    }}
    .panel h4 {{
      margin: 0 0 8px;
      font-size: 14px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .muted {{
      color: var(--muted);
      font-size: 13px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }}
    .tile {{
      display: block;
      border-radius: 12px;
      padding: 18px;
      border: 1px solid rgba(17, 74, 114, 0.14);
      background: rgba(255,255,255,0.78);
      box-shadow: 0 14px 36px rgba(31, 39, 46, 0.06);
    }}
    .tile:hover {{
      text-decoration: none;
      transform: translateY(-1px);
    }}
    .tile-title {{
      margin: 0 0 8px;
      font-size: 22px;
      color: var(--ink);
    }}
    .tile p {{
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 14px;
    }}
    .tile ul, .panel ul {{
      margin: 0 0 0 18px;
      padding: 0;
    }}
    .tile li, .panel li {{
      margin-bottom: 6px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      margin-right: 8px;
      margin-bottom: 8px;
      padding: 0.3rem 0.76rem;
      border-radius: 999px;
      font-size: 12px;
      background: rgba(31, 39, 46, 0.08);
      color: var(--ink);
    }}
    .badge.good {{ background: rgba(22, 95, 79, 0.12); color: var(--good); }}
    .badge.warning {{ background: rgba(168, 97, 18, 0.12); color: var(--warn); }}
    .badge.ghost {{ background: rgba(84, 102, 115, 0.12); color: var(--ghost); }}
    .badge.neutral {{ background: rgba(17, 74, 114, 0.1); color: var(--brand); }}
    .info-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}
    .info-chip {{
      display: flex;
      align-items: baseline;
      gap: 8px;
      padding: 11px 13px;
      border-radius: 16px;
      border: 1px solid rgba(31, 39, 46, 0.08);
      background: rgba(255, 255, 255, 0.7);
      font-size: 13px;
    }}
    .info-chip strong {{
      font-size: 16px;
    }}
    .card {{
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.72);
      padding: 18px;
      margin-bottom: 14px;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
    }}
    .metric-card {{
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.78);
      padding: 18px;
      box-shadow: 0 12px 28px rgba(31, 39, 46, 0.04);
    }}
    .metric-card.good {{
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(22,95,79,0.08));
    }}
    .metric-card.warning {{
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(168,97,18,0.08));
    }}
    .metric-card.neutral {{
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(17,74,114,0.08));
    }}
    .metric-card.ghost {{
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(84,102,115,0.08));
    }}
    .metric-label {{
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .metric-value {{
      font-size: 30px;
      line-height: 1.08;
      letter-spacing: -0.04em;
    }}
    .metric-note {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      min-height: 2.6em;
    }}
    .metric-footer {{
      margin-top: 12px;
    }}
    .metric-footer .badge {{
      margin-bottom: 0;
    }}
    .card-header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      align-items: flex-start;
    }}
    .pair-mark {{
      color: var(--muted);
      font-size: 13px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 10px;
      text-align: left;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .split {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 28px 0;
    }}
    .section-intro {{
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 14px;
    }}
    .report-layout {{
      display: grid;
      grid-template-columns: minmax(320px, 0.95fr) minmax(0, 1.55fr);
      gap: 18px;
      margin-bottom: 18px;
    }}
    .panel-stack {{
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.72);
    }}
    .table-wrap table {{
      min-width: 100%;
      margin: 0;
    }}
    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .rank-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 34px;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      font-size: 12px;
      font-weight: 600;
    }}
    .story-card {{
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.72);
      padding: 16px;
      margin-bottom: 12px;
    }}
    .story-card:last-child {{
      margin-bottom: 0;
    }}
    .story-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .story-title {{
      margin: 0 0 10px;
      font-size: 16px;
      line-height: 1.5;
    }}
    .story-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
      align-items: center;
    }}
    .story-footer {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    .markdown-body {{
      font-size: 15px;
      color: var(--ink);
    }}
    .markdown-body > :first-child {{
      margin-top: 0;
    }}
    .markdown-body > :last-child {{
      margin-bottom: 0;
    }}
    .markdown-body h2,
    .markdown-body h3,
    .markdown-body h4,
    .markdown-body h5 {{
      margin: 1.15rem 0 0.65rem;
      line-height: 1.28;
      letter-spacing: -0.02em;
    }}
    .markdown-body h2 {{
      font-size: 28px;
    }}
    .markdown-body h3 {{
      font-size: 22px;
    }}
    .markdown-body h4 {{
      font-size: 18px;
    }}
    .markdown-body h5 {{
      font-size: 16px;
      color: var(--muted);
    }}
    .markdown-body p {{
      margin: 0 0 0.95rem;
    }}
    .markdown-body ul,
    .markdown-body ol {{
      margin: 0 0 1rem 1.25rem;
      padding: 0;
    }}
    .markdown-body li {{
      margin-bottom: 0.45rem;
    }}
    .markdown-body blockquote {{
      margin: 0 0 1rem;
      padding: 0.9rem 1rem;
      border-left: 4px solid rgba(17, 74, 114, 0.22);
      background: rgba(17, 74, 114, 0.06);
      border-radius: 0 16px 16px 0;
      color: #284455;
    }}
    .markdown-body code {{
      padding: 0.1rem 0.36rem;
      border-radius: 8px;
      background: rgba(31, 39, 46, 0.08);
      font-size: 0.92em;
    }}
    .md-rule {{
      border: 0;
      border-top: 1px solid rgba(31, 39, 46, 0.1);
      margin: 1rem 0 1.1rem;
    }}
    .event-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 18px;
    }}
    .summary-list {{
      list-style: none;
      margin: 0;
      padding: 0;
    }}
    .summary-list li {{
      padding: 12px 0;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
    }}
    .summary-list li:last-child {{
      border-bottom: none;
      padding-bottom: 0;
    }}
    .command-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(300px, 0.9fr);
      gap: 18px;
      align-items: start;
      margin-bottom: 18px;
    }}
    .focus-list {{
      list-style: none;
      margin: 0;
      padding: 0;
    }}
    .focus-list li {{
      display: flex;
      gap: 12px;
      padding: 13px 0;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
      align-items: flex-start;
    }}
    .focus-list li:last-child {{
      border-bottom: none;
    }}
    .focus-index {{
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      font-size: 12px;
      font-weight: 700;
    }}
    .focus-main {{
      flex: 1 1 auto;
      min-width: 0;
    }}
    .focus-actions {{
      flex: 0 0 auto;
      padding-top: 1px;
    }}
    .focus-title {{
      margin: 0 0 4px;
      font-size: 15px;
      font-weight: 700;
      line-height: 1.38;
    }}
    .focus-note {{
      color: var(--muted);
      font-size: 13px;
    }}
    .watch-row {{
      display: grid;
      grid-template-columns: minmax(120px, 1fr) auto;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
      align-items: baseline;
    }}
    .watch-row:last-child {{
      border-bottom: none;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .entry-link {{
      display: block;
      padding: 14px 15px;
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.76);
      min-height: 88px;
    }}
    .entry-link:hover {{
      text-decoration: none;
      border-color: rgba(21, 90, 111, 0.35);
    }}
    .entry-link strong {{
      display: block;
      margin-bottom: 6px;
      color: var(--ink);
      font-size: 15px;
    }}
    .entry-link span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .action-card {{
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.76);
      padding: 14px;
      margin-bottom: 10px;
    }}
    .action-card:last-child {{
      margin-bottom: 0;
    }}
    .action-topline {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 8px;
    }}
    .action-title {{
      margin: 0;
      font-size: 15px;
      line-height: 1.4;
      font-weight: 700;
    }}
    .action-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .button-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }}
    .small-button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.46rem 0.76rem;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      font-size: 12px;
      font-weight: 700;
    }}
    .small-button:hover {{
      text-decoration: none;
      background: #0f4758;
    }}
    .source-link {{
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid rgba(31, 39, 46, 0.08);
    }}
    .report-section {{
      display: grid;
      gap: 18px;
    }}
    .report-block {{
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 12px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.72);
    }}
    .report-block h3 {{
      margin: 0 0 8px;
      font-size: 18px;
      line-height: 1.35;
    }}
    .report-block p {{
      margin: 0 0 10px;
      color: var(--ink);
    }}
    .report-block ul {{
      margin: 0.4rem 0 0 1.2rem;
      padding: 0;
    }}
    .report-block li {{
      margin-bottom: 0.42rem;
    }}
    .report-muted {{
      color: var(--muted);
      font-size: 13px;
    }}
    .report-warning {{
      border-left: 4px solid var(--warn);
      padding-left: 12px;
      color: var(--ink);
    }}
    @media (max-width: 1080px) {{
      .grid-2, .grid-3, .split, .report-layout, .event-grid, .story-grid, .command-layout, .entry-grid {{
        grid-template-columns: 1fr;
      }}
      .focus-list li {{
        flex-wrap: wrap;
      }}
      .focus-actions {{
        width: 100%;
        padding-left: 40px;
      }}
    }}

    /* ============== Today Overview ============== */
    .today-metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }}
    .metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 22px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 12px 32px rgba(31, 39, 46, 0.05);
    }}
    .metric-icon {{
      width: 56px;
      height: 56px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .metric-body {{
      flex: 1;
      min-width: 0;
    }}
    .metric-label {{
      font-size: 14px;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    .metric-value {{
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1.1;
      margin-bottom: 4px;
    }}
    .metric-subtitle {{
      font-size: 12px;
    }}

    .today-grid {{
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 20px;
    }}
    .today-main {{
      margin-bottom: 0;
    }}
    .today-side .panel {{
      margin-bottom: 20px;
    }}
    .today-side .panel:last-child {{
      margin-bottom: 0;
    }}

    .today-section-title {{
      font-size: 18px;
      margin-bottom: 16px;
      letter-spacing: -0.01em;
    }}

    .change-card {{
      display: flex;
      align-items: flex-start;
      gap: 16px;
      padding: 18px;
      border-radius: 12px;
      border: 1px solid rgba(31, 39, 46, 0.08);
      margin-bottom: 12px;
      background: rgba(255, 255, 255, 0.6);
    }}
    .change-card:last-child {{
      margin-bottom: 0;
    }}
    .change-rank {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: var(--brand-soft);
      color: var(--brand);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 16px;
      flex-shrink: 0;
    }}
    .change-body {{
      flex: 1;
      min-width: 0;
    }}
    .change-title {{
      font-weight: 600;
      font-size: 15px;
      margin-bottom: 6px;
      color: var(--ink);
    }}
    .change-entities {{
      font-size: 13px;
      color: var(--brand);
      margin-bottom: 6px;
    }}
    .change-summary {{
      font-size: 13px;
      line-height: 1.5;
    }}
    .change-side {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex-shrink: 0;
      align-items: flex-end;
    }}

    .pending-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 0;
      border-bottom: 1px solid rgba(31, 39, 46, 0.06);
    }}
    .pending-row:last-child {{
      border-bottom: none;
      padding-bottom: 0;
    }}
    .pending-rank {{
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: var(--brand-soft);
      color: var(--brand);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      flex-shrink: 0;
    }}
    .pending-question {{
      flex: 1;
      font-size: 13px;
      color: var(--ink);
    }}

    .coverage-table-wrap {{
      overflow-x: auto;
    }}
    .coverage-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .coverage-table th {{
      text-align: left;
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
      padding: 8px 10px;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .coverage-table td {{
      padding: 10px;
      border-bottom: 1px solid rgba(31, 39, 46, 0.04);
      vertical-align: middle;
    }}
    .coverage-table tr:last-child td {{
      border-bottom: none;
    }}
    .cov-company {{
      font-weight: 500;
    }}
    .status-dot {{
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: middle;
    }}
    .status-dot.tone-good {{ background: #10b981; }}
    .status-dot.tone-warning {{ background: #f59e0b; }}
    .status-dot.tone-danger {{ background: #ef4444; }}
    .status-dot.tone-info {{ background: #3b82f6; }}
    .status-dot.tone-muted {{ background: #94a3b8; }}

    .evidence-bar {{
      display: inline-block;
      width: 60px;
      height: 6px;
      border-radius: 3px;
      background: rgba(31, 39, 46, 0.08);
      vertical-align: middle;
      margin-right: 8px;
    }}
    .evidence-bar-fill {{
      height: 100%;
      border-radius: 3px;
      background: var(--brand);
    }}
    .evidence-pct {{
      font-size: 12px;
      vertical-align: middle;
    }}

    .health-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .health-card {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.5);
      border: 1px solid rgba(31, 39, 46, 0.06);
    }}
    .health-icon {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 700;
      flex-shrink: 0;
      background: rgba(148, 163, 184, 0.12);
      color: #64748b;
    }}
    .health-icon.tone-good {{ background: rgba(16, 185, 129, 0.12); color: #10b981; }}
    .health-icon.tone-warning {{ background: rgba(245, 158, 11, 0.12); color: #f59e0b; }}
    .health-icon.tone-danger {{ background: rgba(239, 68, 68, 0.12); color: #ef4444; }}
    .health-icon.tone-info {{ background: rgba(59, 130, 246, 0.12); color: #3b82f6; }}
    .health-body {{ flex: 1; min-width: 0; }}
    .health-label {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 2px;
    }}
    .health-status {{
      font-size: 14px;
      font-weight: 600;
    }}
    .health-status.tone-good {{ color: #10b981; }}
    .health-status.tone-warning {{ color: #f59e0b; }}
    .health-status.tone-danger {{ color: #ef4444; }}
    .health-status.tone-info {{ color: #3b82f6; }}
    .health-status.tone-muted {{ color: #64748b; }}

    .today-footer {{
      text-align: center;
      padding: 16px 0;
      margin-top: 4px;
    }}

    .today-disclaimer {{
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: var(--muted);
      border-top: 1px solid var(--line);
      margin-top: 8px;
    }}

    .empty-state {{
      padding: 32px 20px;
      text-align: center;
    }}
    .empty-state.small {{
      padding: 20px 16px;
    }}
    .empty-state-title {{
      font-weight: 600;
      font-size: 15px;
      color: var(--ink);
      margin-bottom: 6px;
    }}
    .empty-state-desc {{
      font-size: 13px;
      color: var(--muted);
    }}

    .placeholder-page {{
      text-align: center;
      padding: 80px 20px;
    }}
    .placeholder-icon {{
      font-size: 48px;
      margin-bottom: 20px;
    }}
    .placeholder-title {{
      font-size: 24px;
      margin-bottom: 12px;
    }}
    .placeholder-desc {{
      font-size: 15px;
      color: var(--muted);
      margin-bottom: 16px;
    }}
    .placeholder-note {{
      font-size: 13px;
    }}

    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 500;
      line-height: 1.6;
    }}
    .badge-good {{ background: rgba(16, 185, 129, 0.1); color: #059669; }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.1); color: #d97706; }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.1); color: #dc2626; }}
    .badge-info {{ background: rgba(59, 130, 246, 0.1); color: #2563eb; }}
    .badge-muted {{ background: rgba(148, 163, 184, 0.12); color: #64748b; }}

    .tone-good {{ color: #10b981; }}
    .tone-warning {{ color: #f59e0b; }}
    .tone-danger {{ color: #ef4444; }}
    .tone-info {{ color: #3b82f6; }}
    .tone-muted {{ color: #64748b; }}

    /* ============== Signal Flow ============== */
    .signal-filter-bar {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px 20px;
      margin-bottom: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .filter-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .filter-label {{
      font-size: 13px;
      color: var(--muted);
      white-space: nowrap;
    }}
    .filter-select, .filter-input {{
      padding: 7px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 13px;
      background: #fff;
      color: var(--ink);
      min-width: 120px;
    }}
    .filter-input {{
      min-width: 180px;
    }}
    .filter-reset {{
      margin-left: auto;
      padding: 7px 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 13px;
      background: #fff;
      color: var(--muted);
      cursor: pointer;
      text-decoration: none;
    }}
    .filter-reset:hover {{
      color: var(--brand);
      border-color: var(--brand);
    }}

    .signal-layout {{
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 20px;
    }}

    .timeline-section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 12px 32px rgba(31, 39, 46, 0.05);
    }}
    .section-title {{
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 18px 0;
    }}

    .timeline {{
      position: relative;
      padding-left: 28px;
    }}
    .timeline::before {{
      content: "";
      position: absolute;
      left: 9px;
      top: 6px;
      bottom: 6px;
      width: 2px;
      background: rgba(59, 130, 246, 0.15);
    }}
    .timeline-item {{
      position: relative;
      padding-bottom: 22px;
    }}
    .timeline-item:last-child {{
      padding-bottom: 0;
    }}
    .timeline-node {{
      position: absolute;
      left: -28px;
      top: 4px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #fff;
      border: 3px solid #3b82f6;
      z-index: 1;
    }}
    .timeline-time {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }}

    .signal-card {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px 16px;
    }}
    .signal-title {{
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 6px 0;
      color: var(--ink);
    }}
    .signal-summary {{
      font-size: 13px;
      color: var(--muted);
      line-height: 1.6;
      margin: 0 0 10px 0;
    }}
    .signal-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 10px;
    }}
    .signal-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 500;
      line-height: 1.7;
    }}
    .signal-badge.source {{ background: rgba(59, 130, 246, 0.08); color: #2563eb; }}
    .signal-badge.entity {{ background: rgba(99, 102, 241, 0.08); color: #4f46e5; }}
    .signal-badge.topic {{ background: rgba(139, 92, 246, 0.08); color: #7c3aed; }}
    .signal-badge.strength-high {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .signal-badge.strength-medium {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .signal-badge.strength-low {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .signal-badge.strength-unknown {{ background: rgba(148, 163, 184, 0.12); color: #64748b; }}
    .signal-badge.review {{ background: rgba(251, 146, 60, 0.1); color: #ea580c; }}

    .signal-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .signal-btn {{
      padding: 5px 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--muted);
      text-decoration: none;
      cursor: pointer;
    }}
    .signal-btn:hover {{
      color: var(--brand);
      border-color: var(--brand);
    }}
    .signal-btn.disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}

    .signal-side {{
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .side-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .side-title {{
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 14px 0;
    }}

    .signal-summary-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .summary-stat {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .summary-icon {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      flex-shrink: 0;
    }}
    .summary-icon.blue {{ background: rgba(59, 130, 246, 0.1); color: #2563eb; }}
    .summary-icon.purple {{ background: rgba(139, 92, 246, 0.1); color: #7c3aed; }}
    .summary-icon.red {{ background: rgba(239, 68, 68, 0.1); color: #dc2626; }}
    .summary-icon.amber {{ background: rgba(245, 158, 11, 0.1); color: #d97706; }}
    .summary-number {{
      font-size: 22px;
      font-weight: 700;
      line-height: 1.1;
    }}
    .summary-label {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }}

    .hot-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .hot-chip {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      background: rgba(59, 130, 246, 0.06);
      color: #2563eb;
      border: 1px solid rgba(59, 130, 246, 0.15);
    }}
    .hot-chip.theme {{
      background: rgba(139, 92, 246, 0.06);
      color: #7c3aed;
      border-color: rgba(139, 92, 246, 0.15);
    }}

    .source-bar-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .source-bar-item {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .source-bar-label {{
      font-size: 12px;
      color: var(--muted);
      width: 72px;
      flex-shrink: 0;
    }}
    .source-bar-track {{
      flex: 1;
      height: 6px;
      background: rgba(31, 39, 46, 0.06);
      border-radius: 999px;
      overflow: hidden;
    }}
    .source-bar-fill {{
      height: 100%;
      background: #3b82f6;
      border-radius: 999px;
    }}
    .source-bar-count {{
      font-size: 12px;
      color: var(--muted);
      width: 24px;
      text-align: right;
      flex-shrink: 0;
    }}
    .source-bar-unit {{
      text-align: right;
      font-size: 11px;
      color: var(--muted);
      margin-top: 8px;
    }}

    .signal-empty {{
      text-align: center;
      padding: 48px 20px;
      color: var(--muted);
    }}
    .signal-empty-title {{
      font-size: 15px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 6px;
    }}
    .signal-empty-desc {{
      font-size: 13px;
    }}

    .signal-disclaimer {{
      margin-top: 18px;
      padding: 12px 16px;
      background: rgba(59, 130, 246, 0.04);
      border: 1px solid rgba(59, 130, 246, 0.1);
      border-radius: 10px;
      font-size: 13px;
      color: var(--muted);
    }}

    .load-more {{
      text-align: center;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
    }}
    .load-more-btn {{
      font-size: 13px;
      color: var(--brand);
      cursor: pointer;
    }}

    /* ============== Research Queue ============== */
    .research-page {{
      max-width: 1440px;
      margin: 0 auto;
    }}
    .research-metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .research-metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .research-metric-icon {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }}
    .research-metric-icon.blue {{ background: rgba(59, 130, 246, 0.1); color: #2563eb; }}
    .research-metric-icon.orange {{ background: rgba(249, 115, 22, 0.1); color: #ea580c; }}
    .research-metric-icon.yellow {{ background: rgba(245, 158, 11, 0.1); color: #d97706; }}
    .research-metric-icon.green {{ background: rgba(16, 185, 129, 0.1); color: #059669; }}
    .research-metric-number {{
      font-size: 24px;
      font-weight: 700;
      line-height: 1.1;
    }}
    .research-metric-subtitle {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }}

    .research-layout {{
      display: grid;
      grid-template-columns: 60% 40%;
      gap: 20px;
    }}

    .research-list-section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .research-list-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .research-list-title {{
      font-size: 16px;
      font-weight: 600;
    }}
    .research-filters {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .research-filter-select {{
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
    }}

    .research-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .research-item {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      cursor: pointer;
    }}
    .research-item:hover {{
      border-color: var(--brand);
    }}
    .research-item.selected {{
      border-color: var(--brand);
      background: rgba(59, 130, 246, 0.03);
    }}
    .research-item-rank {{
      width: 26px;
      height: 26px;
      border-radius: 8px;
      background: rgba(59, 130, 246, 0.1);
      color: #2563eb;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 600;
      flex-shrink: 0;
    }}
    .research-item-content {{
      flex: 1;
      min-width: 0;
    }}
    .research-item-title {{
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 4px 0;
      color: var(--ink);
    }}
    .research-item-badges {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      margin-bottom: 6px;
    }}
    .research-item-badge {{
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
    }}
    .research-item-badge.entity {{ background: rgba(99, 102, 241, 0.08); color: #4f46e5; }}
    .research-item-badge.topic {{ background: rgba(139, 92, 246, 0.08); color: #7c3aed; }}
    .research-item-badge.priority-high {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .research-item-badge.priority-medium {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .research-item-badge.priority-low {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .research-item-badge.status-researching {{ background: rgba(59, 130, 246, 0.08); color: #2563eb; }}
    .research-item-badge.status-pending {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .research-item-badge.status-gathering {{ background: rgba(249, 115, 22, 0.08); color: #ea580c; }}
    .research-item-badge.status-deferred {{ background: rgba(148, 163, 184, 0.1); color: #64748b; }}
    .research-item-badge.status-approved {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .research-item-badge.status-rejected {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .research-item-reason {{
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .research-item-meta {{
      display: flex;
      gap: 12px;
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .research-item-actions {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex-shrink: 0;
    }}
    .research-action-btn {{
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 11px;
      background: #fff;
      color: var(--muted);
      cursor: pointer;
      text-decoration: none;
    }}
    .research-action-btn:hover {{
      color: var(--brand);
      border-color: var(--brand);
    }}
    .research-action-btn.approve {{ color: #059669; border-color: rgba(16, 185, 129, 0.3); }}
    .research-action-btn.gather {{ color: #2563eb; border-color: rgba(59, 130, 246, 0.3); }}
    .research-action-btn.defer {{ color: #64748b; border-color: rgba(148, 163, 184, 0.3); }}
    .research-action-btn.reject {{ color: #dc2626; border-color: rgba(239, 68, 68, 0.3); }}

    .research-side {{
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .research-detail-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .research-detail-title {{
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 14px 0;
    }}
    .research-detail-subtitle {{
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--ink);
    }}
    .research-detail-badges {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .research-detail-section {{
      margin-bottom: 16px;
    }}
    .research-detail-section-title {{
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      margin: 0 0 6px 0;
    }}
    .research-detail-text {{
      font-size: 13px;
      color: var(--ink);
      line-height: 1.7;
      white-space: pre-wrap;
    }}
    .research-detail-list {{
      margin: 0;
      padding-left: 18px;
    }}
    .research-detail-list li {{
      font-size: 13px;
      color: var(--ink);
      line-height: 1.7;
      margin-bottom: 4px;
    }}
    .research-empty {{
      text-align: center;
      padding: 32px 16px;
      color: var(--muted);
    }}
    .research-empty-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 4px;
    }}

    .evidence-gap-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .evidence-gap-title {{
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 14px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .evidence-gap-all-link {{
      font-size: 12px;
      color: var(--brand);
      text-decoration: none;
    }}
    .evidence-gap-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .evidence-gap-item {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
    }}
    .evidence-gap-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}
    .evidence-gap-title-text {{
      font-size: 13px;
      font-weight: 600;
      color: var(--ink);
    }}
    .evidence-gap-importance {{
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 4px;
    }}
    .evidence-gap-importance.important {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .evidence-gap-importance.medium {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .evidence-gap-importance.low {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .evidence-gap-meta {{
      display: flex;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
    }}

    .research-disclaimer {{
      margin-top: 18px;
      padding: 12px 16px;
      background: rgba(59, 130, 246, 0.04);
      border: 1px solid rgba(59, 130, 246, 0.1);
      border-radius: 10px;
      font-size: 13px;
      color: var(--muted);
      text-align: center;
    }}

    .research-empty-state {{
      text-align: center;
      padding: 60px 20px;
      color: var(--muted);
    }}
    .research-empty-state-title {{
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 6px;
    }}

    /* Coverage pool styles */
    .coverage-metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }}
    .coverage-metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .coverage-metric-value {{
      font-size: 28px;
      font-weight: 700;
      color: var(--ink);
      margin-bottom: 4px;
    }}
    .coverage-metric-subtitle {{
      font-size: 13px;
      color: var(--muted);
    }}
    .coverage-metric-delta {{
      font-size: 12px;
      color: var(--good);
      margin-top: 4px;
    }}

    .coverage-layout {{
      display: grid;
      grid-template-columns: 58% 40%;
      gap: 20px;
      margin-bottom: 22px;
    }}
    .coverage-table-section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .coverage-table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }}
    .coverage-table-title {{
      font-size: 15px;
      font-weight: 600;
    }}
    .coverage-filter-bar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}
    .coverage-filter-group {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .coverage-filter-label {{
      font-size: 12px;
      color: var(--muted);
    }}
    .coverage-filter-select {{
      padding: 5px 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
    }}
    .coverage-search {{
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
      width: 140px;
    }}

    .coverage-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .coverage-table th {{
      text-align: left;
      padding: 8px 10px;
      font-weight: 600;
      color: var(--muted);
      font-size: 12px;
      border-bottom: 1px solid var(--line);
    }}
    .coverage-table td {{
      padding: 10px;
      border-bottom: 1px solid rgba(31, 39, 46, 0.06);
      vertical-align: middle;
    }}
    .coverage-table tr:hover td {{
      background: rgba(59, 130, 246, 0.02);
    }}
    .coverage-table tr.selected td {{
      background: rgba(59, 130, 246, 0.04);
    }}

    .coverage-progress {{
      height: 6px;
      background: rgba(31, 39, 46, 0.08);
      border-radius: 3px;
      overflow: hidden;
      width: 80px;
    }}
    .coverage-progress-bar {{
      height: 100%;
      background: #3b82f6;
      border-radius: 3px;
      transition: width 0.3s ease;
    }}
    .coverage-progress-bar.high {{ background: #059669; }}
    .coverage-progress-bar.medium {{ background: #d97706; }}
    .coverage-progress-bar.low {{ background: #dc2626; }}

    .coverage-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 500;
    }}
    .coverage-badge.priority-high {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .coverage-badge.priority-medium {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .coverage-badge.priority-low {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .coverage-badge.type-company {{ background: rgba(59, 130, 246, 0.08); color: #2563eb; }}
    .coverage-badge.type-industry {{ background: rgba(139, 92, 246, 0.08); color: #7c3aed; }}
    .coverage-badge.type-theme {{ background: rgba(139, 92, 246, 0.08); color: #7c3aed; }}
    .coverage-badge.status-tracking {{ background: rgba(59, 130, 246, 0.08); color: #2563eb; }}
    .coverage-badge.status-key {{ background: rgba(99, 102, 241, 0.08); color: #4f46e5; }}
    .coverage-badge.status-needs {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .coverage-badge.status-risk {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}

    .coverage-detail-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .coverage-detail-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .coverage-detail-name {{
      font-size: 18px;
      font-weight: 700;
      color: var(--ink);
    }}
    .coverage-detail-badges {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .coverage-detail-section {{
      margin-bottom: 18px;
    }}
    .coverage-detail-section-title {{
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .coverage-focus-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .coverage-focus-chip {{
      padding: 6px 12px;
      border-radius: 8px;
      background: rgba(59, 130, 246, 0.06);
      border: 1px solid rgba(59, 130, 246, 0.12);
      font-size: 12px;
      color: #2563eb;
    }}

    .coverage-signal-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .coverage-signal-item {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 10px 12px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
    }}
    .coverage-signal-title {{
      font-size: 13px;
      font-weight: 500;
      color: var(--ink);
      margin-bottom: 4px;
    }}
    .coverage-signal-meta {{
      font-size: 11px;
      color: var(--muted);
    }}
    .coverage-signal-direction {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 500;
      white-space: nowrap;
    }}
    .coverage-signal-direction.new {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .coverage-signal-direction.improve {{ background: rgba(59, 130, 246, 0.08); color: #2563eb; }}
    .coverage-signal-direction.watch {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .coverage-signal-direction.risk {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .coverage-signal-direction.pending {{ background: rgba(148, 163, 184, 0.1); color: #64748b; }}

    .coverage-evidence-overview {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .coverage-donut {{
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: conic-gradient(
        #3b82f6 0deg var(--p-covered),
        #f59e0b var(--p-covered) var(--p-partial),
        #e5e7eb var(--p-partial) 360deg
      );
      position: relative;
      flex-shrink: 0;
    }}
    .coverage-donut::after {{
      content: "";
      position: absolute;
      inset: 14px;
      border-radius: 50%;
      background: var(--panel);
    }}
    .coverage-donut-label {{
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 700;
      color: var(--ink);
      z-index: 1;
    }}
    .coverage-evidence-legend {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 12px;
    }}
    .coverage-evidence-legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .coverage-evidence-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .coverage-evidence-dot.covered {{ background: #3b82f6; }}
    .coverage-evidence-dot.partial {{ background: #f59e0b; }}
    .coverage-evidence-dot.missing {{ background: #e5e7eb; }}

    .coverage-missing-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .coverage-missing-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 10px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 12px;
    }}
    .coverage-missing-importance {{
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 4px;
    }}
    .coverage-missing-importance.high {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .coverage-missing-importance.medium {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .coverage-missing-importance.low {{ background: rgba(148, 163, 184, 0.1); color: #64748b; }}

    .coverage-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .coverage-chip {{
      padding: 4px 10px;
      border-radius: 6px;
      background: rgba(99, 102, 241, 0.06);
      border: 1px solid rgba(99, 102, 241, 0.12);
      font-size: 12px;
      color: #4f46e5;
    }}

    .coverage-bottom {{
      display: grid;
      grid-template-columns: 1fr 2fr;
      gap: 20px;
      margin-bottom: 22px;
    }}
    .coverage-distribution-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .coverage-distribution-content {{
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .coverage-distribution-donut {{
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: conic-gradient(
        #3b82f6 0deg var(--d-company),
        #7c3aed var(--d-company) var(--d-theme),
        #059669 var(--d-theme) 360deg
      );
      position: relative;
      flex-shrink: 0;
    }}
    .coverage-distribution-donut::after {{
      content: "";
      position: absolute;
      inset: 18px;
      border-radius: 50%;
      background: var(--panel);
    }}
    .coverage-distribution-legend {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 13px;
    }}
    .coverage-distribution-legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .coverage-distribution-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}
    .coverage-distribution-dot.company {{ background: #3b82f6; }}
    .coverage-distribution-dot.theme {{ background: #7c3aed; }}
    .coverage-distribution-dot.industry {{ background: #059669; }}

    .priority-hotzone-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .priority-hotzone-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
    }}
    .hotzone-card {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      text-align: center;
    }}
    .hotzone-card-name {{
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--ink);
    }}
    .hotzone-card-meta {{
      font-size: 11px;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    .hotzone-card-progress {{
      height: 4px;
      background: rgba(31, 39, 46, 0.08);
      border-radius: 2px;
      overflow: hidden;
      margin-top: 8px;
    }}
    .hotzone-card-progress-bar {{
      height: 100%;
      background: #3b82f6;
      border-radius: 2px;
    }}

    .coverage-pagination {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 6px;
      margin-top: 14px;
      font-size: 12px;
    }}
    .coverage-pagination-info {{
      color: var(--muted);
      margin-right: 8px;
    }}
    .coverage-page-btn {{
      padding: 4px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      text-decoration: none;
      font-size: 12px;
    }}
    .coverage-page-btn:hover {{
      border-color: var(--brand);
      color: var(--brand);
    }}
    .coverage-page-btn.active {{
      background: var(--brand);
      color: #fff;
      border-color: var(--brand);
    }}
    .coverage-page-btn.disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}

    .coverage-disclaimer {{
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: var(--muted);
      border-top: 1px solid var(--line);
      margin-top: 8px;
    }}
    .coverage-empty-state {{
      text-align: center;
      padding: 48px 20px;
      color: var(--muted);
    }}
    .coverage-empty-state-title {{
      font-size: 15px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 6px;
    }}

    /* Data health styles */
    .health-metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }}
    .health-metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .health-metric-value {{
      font-size: 22px;
      font-weight: 700;
      color: var(--ink);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .health-metric-subtitle {{
      font-size: 13px;
      color: var(--muted);
    }}
    .health-status-dot {{
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .health-status-dot.normal {{ background: #059669; }}
    .health-status-dot.degraded {{ background: #d97706; }}
    .health-status-dot.blocked {{ background: #dc2626; }}
    .health-status-dot.watching {{ background: #6366f1; }}
    .health-status-dot.pending {{ background: #9ca3af; }}
    .health-status-dot.nodata {{ background: #cbd5e1; }}

    .health-layout {{
      display: grid;
      grid-template-columns: 60% 38%;
      gap: 20px;
      margin-bottom: 22px;
    }}
    .health-issue-section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .health-section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }}
    .health-section-title {{
      font-size: 15px;
      font-weight: 600;
    }}
    .health-section-link {{
      font-size: 12px;
      color: var(--brand);
      text-decoration: none;
    }}
    .health-filter-bar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}
    .health-filter-select {{
      padding: 5px 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
    }}
    .health-search {{
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
      color: var(--ink);
      width: 140px;
    }}

    .health-issue-list {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .health-issue-item {{
      display: flex;
      gap: 14px;
      padding: 14px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 12px;
    }}
    .health-issue-severity {{
      font-size: 12px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 6px;
      flex-shrink: 0;
      height: fit-content;
    }}
    .health-issue-severity.P0 {{ background: rgba(239, 68, 68, 0.1); color: #dc2626; }}
    .health-issue-severity.P1 {{ background: rgba(245, 158, 11, 0.1); color: #d97706; }}
    .health-issue-severity.P2 {{ background: rgba(99, 102, 241, 0.1); color: #4f46e5; }}
    .health-issue-severity.P3 {{ background: rgba(148, 163, 184, 0.1); color: #64748b; }}
    .health-issue-body {{
      flex: 1;
      min-width: 0;
    }}
    .health-issue-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 6px;
    }}
    .health-issue-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--ink);
    }}
    .health-issue-status {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 500;
      flex-shrink: 0;
    }}
    .health-issue-status.blocked {{ background: rgba(239, 68, 68, 0.08); color: #dc2626; }}
    .health-issue-status.degraded {{ background: rgba(245, 158, 11, 0.08); color: #d97706; }}
    .health-issue-status.watching {{ background: rgba(99, 102, 241, 0.08); color: #4f46e5; }}
    .health-issue-status.resolved {{ background: rgba(16, 185, 129, 0.08); color: #059669; }}
    .health-issue-scope {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .health-issue-desc {{
      font-size: 13px;
      color: var(--ink);
      margin-bottom: 8px;
    }}
    .health-issue-meta {{
      font-size: 11px;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
    }}

    .health-side {{
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .health-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 8px 24px rgba(31, 39, 46, 0.04);
    }}
    .health-panel-title {{
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .module-health-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .module-health-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }}
    .module-health-left {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .module-health-status {{
      font-size: 12px;
      color: var(--muted);
    }}

    .health-distribution {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .health-ring {{
      width: 90px;
      height: 90px;
      border-radius: 50%;
      position: relative;
      flex-shrink: 0;
    }}
    .health-ring::after {{
      content: "";
      position: absolute;
      inset: 16px;
      border-radius: 50%;
      background: var(--panel);
    }}
    .health-ring-label {{
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 700;
      color: var(--ink);
      z-index: 1;
    }}
    .health-legend {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      font-size: 12px;
      flex: 1;
    }}
    .health-legend-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}
    .health-legend-left {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .health-legend-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}

    .run-summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}
    .run-summary-item {{
      text-align: center;
      padding: 10px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
    }}
    .run-summary-value {{
      font-size: 18px;
      font-weight: 700;
      color: var(--ink);
      margin-bottom: 2px;
    }}
    .run-summary-label {{
      font-size: 11px;
      color: var(--muted);
    }}

    .health-disclaimer {{
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: var(--muted);
      border-top: 1px solid var(--line);
      margin-top: 8px;
    }}
    .health-empty-state {{
      text-align: center;
      padding: 48px 20px;
      color: var(--muted);
    }}
    .health-empty-state-title {{
      font-size: 15px;
      font-weight: 600;
      color: var(--ink);
      margin-bottom: 6px;
    }}

    @media (max-width: 1080px) {{
      .today-metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .today-grid {{
        grid-template-columns: 1fr;
      }}
      .health-grid {{
        grid-template-columns: 1fr;
      }}
      .signal-layout {{
        grid-template-columns: 1fr;
      }}
      .research-metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .research-layout {{
        grid-template-columns: 1fr;
      }}
      .coverage-metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .coverage-layout {{
        grid-template-columns: 1fr;
      }}
      .coverage-bottom {{
        grid-template-columns: 1fr;
      }}
      .health-metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .health-layout {{
        grid-template-columns: 1fr;
      }}
    }}

  </style>
</head>
<body>
  <div class="page">
    <header class="topbar">
      <div class="brand">同行资本投研系统</div>
      <nav class="nav">{render_nav(current_path)}</nav>
    </header>
    {status_strip_html}
    <section class="hero">
      <h1>{escape(hero_title)}</h1>
      <p>{escape(hero_subtitle)}</p>
      {facts_html}
    </section>
    {body}
  </div>
{auto_refresh_script}
</body>
</html>"""


def shell_state_kwargs(state: dict | None) -> dict[str, str | None]:
    snapshot = state or {}
    return {
        "snapshot_generated_at": snapshot.get("generated_at"),
        "state_version": snapshot.get("state_version"),
    }


def render_kv_chips(items: list[tuple[str, str | int | float | None]], chip_class: str = "info-chip") -> str:
    chips = []
    for label, value in items:
        display_label = code_label(str(label or "-"))
        display_value = fmt_number(value) if isinstance(value, (int, float)) else code_label(str(value or "-"))
        chips.append(
            f"<div class='{chip_class}'>"
            f"<span>{escape(display_label)}</span>"
            f"<strong>{escape(display_value)}</strong>"
            "</div>"
        )
    return "".join(chips)


def render_metric_grid(metrics: list[dict[str, str | None]]) -> str:
    cards = []
    for item in metrics:
        tone = item.get("tone") or "neutral"
        title = escape(str(item.get("title") or "-"))
        value = escape(str(item.get("value") or "-"))
        note = escape(str(item.get("note") or ""))
        footer_html = item.get("footer_html") or ""
        footer_block = f"<div class='metric-footer'>{footer_html}</div>" if footer_html else ""
        cards.append(
            "<article class='metric-card "
            f"{escape(tone)}'>"
            f"<div class='metric-label'>{title}</div>"
            f"<div class='metric-value'>{value}</div>"
            f"<div class='metric-note'>{note}</div>"
            f"{footer_block}"
            "</article>"
        )
    return "<section class='metric-grid'>" + "".join(cards) + "</section>"


def replace_code_tokens(text: str) -> str:
    result = text
    for token, label in CODE_LABELS.items():
        result = re.sub(rf"\b{re.escape(token)}\b", label, result)
    return result


def render_inline_markdown(text: str | None) -> str:
    source = replace_code_tokens(str(text or "").strip())
    if not source:
        return ""

    parts: list[str] = []
    cursor = 0
    for match in INLINE_TOKEN_RE.finditer(source):
        if match.start() > cursor:
            parts.append(escape(source[cursor : match.start()]))
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            parts.append(f"<strong>{escape(token[2:-2])}</strong>")
        elif token.startswith("`") and token.endswith("`"):
            parts.append(f"<code>{escape(token[1:-1])}</code>")
        else:
            link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token)
            if link_match:
                label, href = link_match.groups()
                parts.append(
                    f"<a href='{escape(href, quote=True)}' target='_blank' rel='noreferrer'>{escape(label)}</a>"
                )
            else:
                parts.append(escape(token))
        cursor = match.end()
    if cursor < len(source):
        parts.append(escape(source[cursor:]))
    return "".join(parts)


def looks_like_table_separator(line: str) -> bool:
    return bool(TABLE_SEPARATOR_RE.match(line.strip()))


def parse_pipe_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def is_pipe_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return "|" in lines[index] and looks_like_table_separator(lines[index + 1])


def is_markdown_block_start(lines: list[str], index: int) -> bool:
    line = lines[index].strip()
    if not line:
        return True
    return bool(
        HEADING_RE.match(line)
        or re.fullmatch(r"[-*_]{3,}", line)
        or line.startswith(">")
        or UNORDERED_LIST_RE.match(line)
        or ORDERED_LIST_RE.match(line)
        or is_pipe_table_start(lines, index)
    )


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_html = "".join(f"<th>{render_inline_markdown(cell)}</th>" for cell in headers)
    body_rows = []
    for row in rows:
        normalized = row + [""] * max(0, len(headers) - len(row))
        cells = "".join(f"<td>{render_inline_markdown(cell)}</td>" for cell in normalized[: len(headers)])
        body_rows.append(f"<tr>{cells}</tr>")
    if not body_rows:
        body_rows.append(f"<tr><td colspan='{len(headers)}' class='empty'>暂无表格数据</td></tr>")
    return (
        "<div class='table-wrap'>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )


def markdown_to_html(text: str | None) -> str:
    source = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not source.strip():
        return "<div class='empty'>暂无内容。</div>"

    lines = source.split("\n")
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        if is_pipe_table_start(lines, index):
            headers = parse_pipe_row(lines[index])
            rows: list[list[str]] = []
            index += 2
            while index < len(lines):
                current = lines[index].strip()
                if not current or "|" not in current:
                    break
                rows.append(parse_pipe_row(lines[index]))
                index += 1
            blocks.append(render_markdown_table(headers, rows))
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            level = min(len(heading_match.group(1)) + 1, 5)
            blocks.append(f"<h{level}>{render_inline_markdown(heading_match.group(2))}</h{level}>")
            index += 1
            continue

        if re.fullmatch(r"[-*_]{3,}", stripped):
            blocks.append("<hr class='md-rule'>")
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines):
                current = lines[index].strip()
                if not current.startswith(">"):
                    break
                quote_lines.append(current[1:].lstrip())
                index += 1
            blocks.append(f"<blockquote><p>{render_inline_markdown(' '.join(quote_lines))}</p></blockquote>")
            continue

        list_match = UNORDERED_LIST_RE.match(stripped) or ORDERED_LIST_RE.match(stripped)
        if list_match:
            ordered = bool(ORDERED_LIST_RE.match(stripped))
            pattern = ORDERED_LIST_RE if ordered else UNORDERED_LIST_RE
            items: list[str] = []
            while index < len(lines):
                current = lines[index].strip()
                current_match = pattern.match(current)
                if not current_match:
                    break
                items.append(f"<li>{render_inline_markdown(current_match.group(1))}</li>")
                index += 1
            tag = "ol" if ordered else "ul"
            blocks.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        paragraph_lines: list[str] = []
        while index < len(lines):
            current = lines[index].strip()
            if not current:
                break
            if paragraph_lines and is_markdown_block_start(lines, index):
                break
            paragraph_lines.append(current)
            index += 1
        blocks.append(f"<p>{render_inline_markdown(' '.join(paragraph_lines))}</p>")

    return "".join(blocks) if blocks else "<div class='empty'>暂无内容。</div>"


def render_markdown_block(text: str | None) -> str:
    return f"<div class='markdown-body'>{markdown_to_html(text)}</div>"


def read_artifact_text(artifact: dict | None) -> str | None:
    if not artifact:
        return None
    path_value = artifact.get("abs_path") or artifact.get("rel_path")
    artifact_path = resolve_project_path(path_value)
    if artifact_path is None or not artifact_path.exists() or not artifact_path.is_file():
        return None
    try:
        return artifact_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return artifact_path.read_text(encoding="utf-8", errors="replace")


def render_pool_badges(pool_types: str | None) -> str:
    labels = [item.strip() for item in str(pool_types or "").split(",") if item.strip()]
    if not labels:
        return "<span class='muted'>-</span>"
    return "<div class='badge-row'>" + "".join(badge(label, "ghost") for label in labels) + "</div>"


def fmt_money_cn(value: float | int | None) -> str:
    if value in (None, ""):
        return "-"
    amount = float(value)
    abs_amount = abs(amount)
    if abs_amount >= 100000000:
        return f"{amount / 100000000:,.2f} 亿元"
    if abs_amount >= 10000:
        return f"{amount / 10000:,.2f} 万元"
    return fmt_number(amount)


def fmt_shares_cn(value: float | int | None) -> str:
    if value in (None, ""):
        return "-"
    amount = float(value)
    abs_amount = abs(amount)
    if abs_amount >= 100000000:
        return f"{amount / 100000000:,.2f} 亿股/份"
    if abs_amount >= 10000:
        return f"{amount / 10000:,.2f} 万股/份"
    return fmt_number(amount)


def render_rank_badge(index: int) -> str:
    return f"<span class='rank-badge'>#{index}</span>"


def render_html_table(headers: list[str], rows: list[list[str]], empty_text: str = "暂无数据") -> str:
    if rows:
        body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    else:
        body = f"<tr><td colspan='{len(headers)}' class='empty'>{escape(empty_text)}</td></tr>"
    header_html = "".join(f"<th>{escape(column)}</th>" for column in headers)
    return (
        "<div class='table-wrap'>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
        "</div>"
    )


def ts_code_from_slug(slug: str | None) -> str | None:
    if slug in (None, ""):
        return None
    match = re.fullmatch(r"(\d{5,6})_(sz|sh|hk)", str(slug).lower())
    if not match:
        return None
    code, market = match.groups()
    return f"{code}.{market.upper()}"


def entity_label_from_slug(slug: str | None) -> str | None:
    if slug in (None, ""):
        return None
    text = str(slug).strip().lower()
    if not text:
        return None
    code = ts_code_from_slug(text)
    if code:
        return code
    stock_market_match = re.fullmatch(r"([a-z0-9]+)_(us|hk|sz|sh|bj|ai)", text)
    if stock_market_match:
        symbol, market = stock_market_match.groups()
        if market == "hk" and symbol.isdigit():
            return f"{symbol}.{market.upper()}"
        return symbol.upper()
    pure_symbol = re.fullmatch(r"[a-z][a-z0-9.-]{0,15}", text)
    if pure_symbol:
        return text.upper()
    return None


def guess_source_label(rel_path: str | None) -> str:
    if rel_path in (None, ""):
        return "参考材料"
    path = Path(rel_path)
    name = path.name
    rel = str(rel_path)

    if rel.startswith("04_portfolio/actions/"):
        return "组合动作建议"
    if rel.startswith("04_portfolio/rotation/"):
        return "轮动候选快照"
    if rel.startswith("04_portfolio/execution_plans/"):
        return "轮动执行计划"
    if rel.startswith("02_research/objective_monitor/"):
        return "客观监控总表"
    if rel.startswith("02_research/strategy_watch/"):
        if name == "00_strategy_watch_batch.md":
            return "策略观察总表"
        code = ts_code_from_slug(name.replace("_strategy_watch.md", ""))
        return f"{code or '单票'} 策略卡"
    if rel.startswith("06_reports/daily/"):
        return "日报原文"
    if rel.startswith("11_smr_wiki/raw/external/stock/"):
        stock_code = entity_label_from_slug(path.parts[4] if len(path.parts) > 4 else None)
        if "__ir_material_page__" in name:
            return f"{stock_code or '相关标的'} 公司 IR 原文"
        if "__ir_material_pdf__" in name:
            return f"{stock_code or '相关标的'} 公司 IR PDF"
        if "__sec_earnings_material__" in name:
            return f"{stock_code or '相关标的'} SEC 业绩附件"
        if "__sec_filing_document__" in name:
            return f"{stock_code or '相关标的'} SEC 主文件"
        if "__sec_submissions_json__" in name:
            return f"{stock_code or '相关标的'} SEC 提交清单"
        if "__public_analyst_signal__" in name:
            return f"{stock_code or '相关标的'} 公开卖方摘要"
        if "__public_transcript__" in name:
            return f"{stock_code or '相关标的'} 公开电话会文字稿"
        if "__announcement__" in name:
            lower_name = name.lower()
            if "_hk" in lower_name:
                return f"{stock_code or '相关标的'} 港交所公告"
            if any(token in lower_name for token in ("_sz", "_sh", "_bj")):
                return f"{stock_code or '相关标的'} 巨潮原文"
            return f"{stock_code or '相关标的'} 公告原文"
        if "__research" in name:
            return f"{stock_code or '相关标的'} 外部研报"
        if "__news" in name:
            return f"{stock_code or '相关标的'} 资讯原文"
        return f"{stock_code or '相关标的'} 参考材料"
    return path.stem.replace("_", " ")


def link_for_rel_path(rel_path: str | None, label: str | None = None) -> str:
    if not rel_path:
        return "<span class='muted'>暂无原文</span>"
    href = f"/artifact?path={quote(rel_path)}"
    display = label or guess_source_label(rel_path)
    return f"<a href='{href}'>{escape(display)}</a>"


def render_source_list(rel_paths: list[str] | None, empty_text: str = "暂无原文入口。") -> str:
    ordered: list[str] = []
    seen: set[str] = set()
    for rel_path in rel_paths or []:
        if not rel_path or rel_path in seen:
            continue
        seen.add(rel_path)
        ordered.append(rel_path)
    if not ordered:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    items = "".join(f"<li>{link_for_rel_path(rel_path)}</li>" for rel_path in ordered)
    return f"<ul class='summary-list'>{items}</ul>"


def iter_unique_watch_items(state: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for bucket in (
        state.get("strategy_watch", {}).get("all_items") or [],
        state.get("strategy_watch", {}).get("top_focus_items") or [],
        state.get("rotation", {}).get("top_add_candidates") or [],
        state.get("rotation", {}).get("top_reduce_candidates") or [],
    ):
        for item in bucket:
            ts_code = item.get("ts_code")
            if not ts_code or ts_code in seen:
                continue
            seen.add(ts_code)
            items.append(item)
    return items


def find_watch_item(state: dict, ts_code: str | None) -> dict | None:
    if ts_code in (None, ""):
        return None
    for item in iter_unique_watch_items(state):
        if item.get("ts_code") == ts_code:
            return item
    return None


def find_action(state: dict, action_id: str | None) -> dict | None:
    if action_id in (None, ""):
        return None
    for action in state.get("portfolio_action", {}).get("actions") or []:
        if action.get("action_id") == action_id:
            return action
    return None


def detail_context_for_symbol(state: dict, ts_code: str | None) -> dict:
    if ts_code in (None, ""):
        return {}
    return ((state.get("detail_context") or {}).get("by_ts_code") or {}).get(ts_code, {})


def action_management_quote_rows(state: dict, action: dict) -> list[dict]:
    rows = []
    for role_label, stock in (
        ("调入腿", action.get("add") or {}),
        ("调出腿", action.get("remove") or {}),
        ("复核对象", action.get("subject") or {}),
    ):
        ts_code = stock.get("ts_code")
        if not ts_code:
            continue
        watch_item = find_watch_item(state, ts_code) or {}
        context = detail_context_for_symbol(state, ts_code)
        transcript = context.get("public_transcript") or {}
        status_item = transcript or watch_item or {}
        rows.append(
            {
                "role_label": role_label,
                "name": stock.get("name") or watch_item.get("name") or ts_code,
                "ts_code": ts_code,
                "status": transcript_status_code(status_item),
                "status_text": transcript_status_sentence(status_item, 82),
                "source_rel_path": transcript.get("source_rel_path") or watch_item.get("public_transcript_source_rel_path"),
            }
        )
    return rows


def action_management_quote_brief(state: dict, action: dict) -> str:
    rows = action_management_quote_rows(state, action)
    if not rows:
        return "当前没有关联到可判断原话状态的标的。"
    parts = [f"{row['role_label']} {row['name']} {code_label(row['status'])}" for row in rows]
    statuses = {row["status"] for row in rows}
    if statuses <= {"missing"}:
        tail = "当前主要靠趋势、公告和研究锚点支撑。"
    elif "fresh" in statuses or "usable" in statuses:
        tail = "至少一侧有可用原话可复核。"
    else:
        tail = "现有原话都偏旧，只能当背景资料。"
    return f"{'；'.join(parts)}。{tail}"


def action_management_quote_fact(state: dict, action: dict) -> str:
    rows = action_management_quote_rows(state, action)
    if not rows:
        return "-"
    return " / ".join(f"{row['role_label']}{code_label(row['status'])}" for row in rows)


def render_watch_name_link(item: dict) -> str:
    ts_code = item.get("ts_code")
    name = item.get("name") or ts_code or "-"
    href = research_detail_href(ts_code)
    return (
        f"<a href='{href}'><strong>{escape(name)}</strong></a>"
        f"<div class='muted'>{escape(ts_code or '-')} · {escape(code_label(item.get('sector')))}</div>"
    )


def render_action_title_link(action: dict) -> str:
    action_id = action.get("action_id")
    title = action.get("title") or "-"
    if not action_id:
        return f"<strong>{escape(title)}</strong>"
    return f"<a href='{action_detail_href(action_id)}'><strong>{escape(title)}</strong></a>"


def render_symbol_events_panel(events: list[dict], title: str = "最近事件") -> str:
    if not events:
        content = "<div class='empty'>当前没有抓到新的事件。</div>"
    else:
        blocks = []
        for event in events[:5]:
            summary_html = (
                f"<div class='muted' style='margin-top:6px'>{escape(business_text(event.get('summary') or '', 96))}</div>"
                if event.get("summary")
                else ""
            )
            blocks.append(
                "<li>"
                f"<div>{badge(event.get('calendar_kind') or event.get('event_family'), 'ghost')}{badge(event.get('importance'), 'neutral')}</div>"
                f"<div style='margin-top:6px'>{escape(replace_code_tokens(event.get('title') or '-'))}</div>"
                f"{summary_html}"
                f"<div class='muted' style='margin-top:6px'>{escape(event.get('publish_time') or event.get('event_date') or '-')}</div>"
                f"<div class='muted' style='margin-top:4px'>{link_for_rel_path(event.get('source_rel_path'), '查看原文') if event.get('source_rel_path') else '暂无原文'}</div>"
                "</li>"
            )
        content = f"<ul class='summary-list'>{''.join(blocks)}</ul>"
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>看这个标的最近到底发生了什么，而不是只看一句摘要。</div>"
        f"{content}"
        "</article>"
    )


def render_symbol_capital_flow_panel(context: dict) -> str:
    margin = context.get("margin_balance")
    stock_connect_hits = context.get("stock_connect_hits") or []
    fact_sheet = context.get("capital_flow_fact_sheet") or {}
    margin_facts = fact_sheet.get("margin_balance") or {}
    stock_connect_facts = fact_sheet.get("stock_connect") or {}
    parts = []
    if margin_facts.get("summary_line"):
        parts.append(
            "<li>"
            "<div><strong>两融随时口径</strong></div>"
            f"<div class='muted'>{escape(live_business_text(margin_facts.get('summary_line')))}</div>"
            "</li>"
        )
    if margin:
        parts.append(
            "<li>"
            f"<div><strong>两融命中</strong></div>"
            f"<div class='muted'>随时：{escape(margin.get('trade_date') or '-')} / {escape(code_label(margin.get('exchange')))}</div>"
            f"<div class='muted'>融资余额：{escape(fmt_money_cn(margin.get('financing_balance')))} / 融资买入额：{escape(fmt_money_cn(margin.get('financing_buy_amount')))}</div>"
            f"<div class='muted'>融券余量：{escape(fmt_shares_cn(margin.get('securities_lending_balance_volume')))}</div>"
            "</li>"
        )
    if stock_connect_facts.get("summary_line"):
        parts.append(
            "<li>"
            "<div><strong>互联互通随时口径</strong></div>"
            f"<div class='muted'>{escape(live_business_text(stock_connect_facts.get('summary_line')))}</div>"
            f"<div class='muted' style='margin-top:4px'>{escape(live_business_text(stock_connect_facts.get('holding_line') or ''))}</div>"
            "</li>"
        )
    for hit in stock_connect_hits[:3]:
        parts.append(
            "<li>"
            f"<div><strong>{escape(hit.get('route_name') or '互联互通')}</strong></div>"
            f"<div class='muted'>方向：{escape(code_label(hit.get('direction')))} / 频率：{escape(code_label(hit.get('frequency')))} / 随时：{escape(hit.get('trade_date') or '-')}</div>"
            f"<div class='muted'>持股数量：{escape(fmt_shares_cn(hit.get('holding_quantity')))}</div>"
            "</li>"
        )
    content = f"<ul class='summary-list'>{''.join(parts)}</ul>" if parts else "<div class='empty'>当前没有资金流命中。</div>"
    return (
        "<article class='panel'>"
        "<h2>资金流命中</h2>"
        "<div class='section-intro'>把这个标的在两融和互联互通里的最新命中情况放在一起看，并明确标出对应的官方随时日期。</div>"
        f"{content}"
        "</article>"
    )


def render_capital_flow_fact_panel(capital: dict) -> str:
    margin = (capital or {}).get("margin_balance") or {}
    stock_connect = (capital or {}).get("stock_connect") or {}
    rows = []
    if margin.get("fact_summary_line"):
        rows.append(
            "<li>"
            "<div><strong>两融</strong></div>"
            f"<div class='muted'>{escape(live_business_text(margin.get('fact_summary_line')))}</div>"
            "</li>"
        )
    if stock_connect.get("fact_summary_line"):
        rows.append(
            "<li>"
            "<div><strong>互联互通日频路线</strong></div>"
            f"<div class='muted'>{escape(live_business_text(stock_connect.get('fact_summary_line')))}</div>"
            "</li>"
        )
    if stock_connect.get("holding_summary_line"):
        rows.append(
            "<li>"
            "<div><strong>互联互通持股口径</strong></div>"
            f"<div class='muted'>{escape(live_business_text(stock_connect.get('holding_summary_line')))}</div>"
            "</li>"
        )
    if stock_connect.get("probe_line"):
        rows.append(
            "<li>"
            "<div><strong>北向实时试探</strong></div>"
            f"<div class='muted'>{escape(live_business_text(stock_connect.get('probe_line')))}</div>"
            "</li>"
        )
    if stock_connect.get("estimate_line"):
        rows.append(
            "<li>"
            "<div><strong>北向估算规则</strong></div>"
            f"<div class='muted'>{escape(live_business_text(stock_connect.get('estimate_line')))}</div>"
            "</li>"
        )
    content = f"<ul class='summary-list'>{''.join(rows)}</ul>" if rows else "<div class='empty'>当前没有可读的资金流事实说明。</div>"
    return (
        "<article class='panel'>"
        "<h2>资金流随时口径</h2>"
        "<div class='section-intro'>这里专门说明今天资金流到底更新到了哪一天，避免把分频率数据误读成同一口径。</div>"
        f"{content}"
        "<div class='story-footer' style='margin-top:12px'><a href='/capital-flow'>去资金流页看完整明细</a></div>"
        "</article>"
    )


def render_market_fact_panel(overview: dict, capital: dict, title: str = "数据事实口径") -> str:
    overview = overview or {}
    capital = capital or {}
    margin = (capital.get("margin_balance") or {})
    stock_connect = (capital.get("stock_connect") or {})
    rows = [
        (
            "A股行情",
            f"当前页面默认按 {overview.get('a_share_trade_date') or '-'} 的行情随时展示，"
            f"相对今天 {fmt_lag_days(overview.get('a_share_trade_lag_days'))}。"
        ),
        (
            "港股行情",
            f"当前页面默认按 {overview.get('hk_trade_date') or '-'} 的行情随时展示，"
            f"相对今天 {fmt_lag_days(overview.get('hk_trade_lag_days'))}。"
        ),
        (
            "美股行情",
            f"当前页面默认按 {overview.get('us_trade_date') or '-'} 的行情随时展示，"
            f"相对今天 {fmt_lag_days(overview.get('us_trade_lag_days'))}。"
        ),
    ]
    if margin.get("fact_summary_line"):
        rows.append(("两融", relabel_live_copy(margin.get("fact_summary_line"))))
    if stock_connect.get("fact_summary_line"):
        rows.append(("互联互通日频", relabel_live_copy(stock_connect.get("fact_summary_line"))))
    if stock_connect.get("holding_summary_line"):
        rows.append(("互联互通持股", relabel_live_copy(stock_connect.get("holding_summary_line"))))

    content = "".join(
        "<li>"
        f"<div><strong>{escape(label)}</strong></div>"
        f"<div class='muted'>{escape(business_text(text))}</div>"
        "</li>"
        for label, text in rows
        if text
    )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>统一说明这一页到底按哪一天的随时口径在看，避免把实时试探口径和官方落地日期混着理解。</div>"
        f"<ul class='summary-list'>{content}</ul>"
        "</article>"
    )


def render_symbol_risk_panel(context: dict) -> str:
    risk_alerts = context.get("risk_alerts") or []
    open_position = context.get("open_position")
    parts = []
    if open_position:
        parts.append(
            "<li>"
            "<div><strong>当前持仓参考</strong></div>"
            f"<div class='muted'>开仓日：{escape(open_position.get('entry_date') or '-')} / 成本：{escape(fmt_number(open_position.get('cost')))}</div>"
            f"<div class='muted'>持股数：{escape(fmt_number(open_position.get('shares')))} / 浮盈亏：{escape(fmt_number(open_position.get('pnl')))} / 浮盈亏比例：{escape(fmt_pct(open_position.get('pnl_pct')))}</div>"
            "</li>"
        )
    for alert in risk_alerts[:3]:
        parts.append(
            "<li>"
            f"<div>{badge(alert.get('severity'), 'warning')}{badge(alert.get('alert_type'), 'ghost')}</div>"
            f"<div style='margin-top:6px'>{escape(business_text(alert.get('message') or '-'))}</div>"
            f"<div class='muted' style='margin-top:6px'>时间：{escape(alert.get('alert_time') or '-')}</div>"
            f"<div class='muted'>建议动作：{escape(business_text(alert.get('action') or '-'))}</div>"
            "</li>"
        )
    content = f"<ul class='summary-list'>{''.join(parts)}</ul>" if parts else "<div class='empty'>当前没有风险命中。</div>"
    return (
        "<article class='panel'>"
        "<h2>风险与持仓</h2>"
        "<div class='section-intro'>如果这个标的有持仓参考或风险提醒，这里会直接展示出来。</div>"
        f"{content}"
        "</article>"
    )


def render_symbol_compare_panel(title: str, left_label: str, left_item: dict | None, right_label: str, right_item: dict | None, state: dict) -> str:
    left_context = detail_context_for_symbol(state, (left_item or {}).get("ts_code"))
    right_context = detail_context_for_symbol(state, (right_item or {}).get("ts_code"))

    def snapshot_text(item: dict | None, field: str) -> str:
        if not item:
            return "-"
        return str(item.get(field) or "-")

    def money_or_dash(value: float | int | None) -> str:
        return fmt_money_cn(value) if value not in (None, "") else "-"

    def stock_connect_text(context: dict) -> str:
        hits = context.get("stock_connect_hits") or []
        if not hits:
            return "-"
        head = hits[0]
        return (
            f"{head.get('route_name') or '-'} / {fmt_shares_cn(head.get('holding_quantity'))} / "
            f"{code_label(head.get('frequency'))} / {head.get('trade_date') or '-'}"
        )

    rows = [
        [
            "当前口径",
            f"{code_label(snapshot_text(left_item, 'primary_pool'))} / {code_label(snapshot_text(left_item, 'objective_view'))} / {code_label(snapshot_text(left_item, 'priority'))}",
            f"{code_label(snapshot_text(right_item, 'primary_pool'))} / {code_label(snapshot_text(right_item, 'objective_view'))} / {code_label(snapshot_text(right_item, 'priority'))}",
        ],
        [
            "趋势判断",
            business_text((left_item or {}).get("trend_summary") or "-"),
            business_text((right_item or {}).get("trend_summary") or "-"),
        ],
        [
            "主要矛盾",
            focus_tension_text(left_item or {}),
            focus_tension_text(right_item or {}),
        ],
        [
            "电话会原话",
            f"{code_label(((left_context.get('public_transcript') or {}).get('freshness_label')) or snapshot_text(left_item, 'public_transcript_freshness'))} / {compact_text(public_transcript_summary((left_context.get('public_transcript') or left_item or {})), 78)}",
            f"{code_label(((right_context.get('public_transcript') or {}).get('freshness_label')) or snapshot_text(right_item, 'public_transcript_freshness'))} / {compact_text(public_transcript_summary((right_context.get('public_transcript') or right_item or {})), 78)}",
        ],
        [
            "最新表现",
            f"收盘 {fmt_number((left_item or {}).get('latest_close'))} / 日涨跌 {fmt_pct((left_item or {}).get('latest_pct_chg'))}",
            f"收盘 {fmt_number((right_item or {}).get('latest_close'))} / 日涨跌 {fmt_pct((right_item or {}).get('latest_pct_chg'))}",
        ],
        [
            "最近事件",
            f"{len(left_context.get('recent_events') or [])} 条",
            f"{len(right_context.get('recent_events') or [])} 条",
        ],
        [
            "两融命中",
            money_or_dash((left_context.get("margin_balance") or {}).get("financing_balance")),
            money_or_dash((right_context.get("margin_balance") or {}).get("financing_balance")),
        ],
        [
            "互联互通",
            stock_connect_text(left_context),
            stock_connect_text(right_context),
        ],
    ]
    html_rows = [[escape(cell) for cell in row] for row in rows]
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>把换入腿和换出腿放在一张表里，先看结构差异，再决定是否继续深挖。</div>"
        f"{render_html_table(['维度', left_label, right_label], html_rows, '暂无对比数据。')}"
        "</article>"
    )


def as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def action_proxy_score(action: dict) -> float | None:
    for text in action.get("rationale") or []:
        match = re.search(r"结构改善代理分\s*`?([0-9]+(?:\.[0-9]+)?)`?", str(text))
        if match:
            return as_float(match.group(1))
    return None


def action_forecast_context(state: dict, item: dict | None) -> dict:
    if not item:
        return {}
    context = detail_context_for_symbol(state, item.get("ts_code"))
    return context.get("forecast") or {}


def window_bias_pct(forecast: dict | None, window_key: str) -> float | None:
    window = (forecast or {}).get(window_key) or {}
    return as_float(window.get("bias_pct"))


def fmt_bias_delta(value: float | None) -> str:
    return fmt_pct(value) if value is not None else "-"


def action_target_price_text(item: dict | None, context: dict | None) -> str:
    external = (context or {}).get("external_research") or {}
    target = external.get("target_price_yuan") or (item or {}).get("target_price_yuan")
    if target not in (None, ""):
        return f"外部研报目标价 {fmt_number(target)}"
    return "当前没有统一目标价口径；这条动作只能按受控试单和观察/失效位推进，不能当成目标价驱动的满仓交易。"


def external_research_fact(item: dict | None, context: dict | None) -> str:
    external = (context or {}).get("external_research") or {}
    if not external and not item:
        return "暂无外部研究锚点。"
    parts = []
    org = external.get("org_name") or (item or {}).get("external_research_org")
    rating = external.get("rating_name") or (item or {}).get("external_research_rating")
    published = external.get("published_at") or (item or {}).get("external_research_published_at")
    if org:
        parts.append(org)
    if rating:
        parts.append(rating)
    if published:
        parts.append(published)
    eps = external.get("eps_yuan") or {}
    pe = external.get("pe_multiple") or {}
    if eps:
        latest_key = sorted(eps.keys())[0]
        parts.append(f"EPS {latest_key}={fmt_number(eps.get(latest_key))}")
    if pe:
        latest_key = sorted(pe.keys())[0]
        parts.append(f"PE {latest_key}={fmt_number(pe.get(latest_key))}")
    return " / ".join(parts) if parts else external_research_summary(external or item or {})


def capital_flow_fact(context: dict | None) -> str:
    context = context or {}
    margin = context.get("margin_balance") or {}
    stock_connect_hits = context.get("stock_connect_hits") or []
    parts = []
    if margin:
        parts.append(
            f"两融余额 {fmt_money_cn(margin.get('financing_balance'))}"
            f" / 单日融资买入 {fmt_money_cn(margin.get('financing_buy_amount'))}"
            f" / {margin.get('trade_date') or '-'}"
        )
    if stock_connect_hits:
        head = stock_connect_hits[0]
        parts.append(
            f"{head.get('route_name') or '-'}持有 {fmt_shares_cn(head.get('holding_quantity'))}"
            f" / {code_label(head.get('frequency'))}"
            f" / {head.get('trade_date') or '-'}"
        )
    return "；".join(parts) if parts else "暂无资金面锚点。"


def action_price_line(item: dict | None, forecast: dict | None) -> str:
    item = item or {}
    forecast = forecast or {}
    return (
        f"最新价 {fmt_number(item.get('latest_close') or forecast.get('latest_close'))}"
        f" / 日涨跌 {fmt_pct(item.get('latest_pct_chg') if item.get('latest_pct_chg') is not None else forecast.get('latest_pct_chg'))}"
        f" / MA20 {fmt_number(forecast.get('ma_20'))}"
        f" / MA60 {fmt_number(forecast.get('ma_60'))}"
        f" / 趋势强度 {fmt_number(forecast.get('trend_strength'))}"
    )


def paper_watch_line(state: dict, ts_code: str | None) -> str:
    ticket = find_paper_watch_ticket(((state.get("current_state") or {}).get("paper_watch") or []), ts_code)
    if not ticket:
        return "暂无纸面观察上下沿，需用下一轮区间/风控链补齐。"
    return f"观察上沿 {fmt_number(ticket.get('observe_above'))}；失效下沿 {fmt_number(ticket.get('invalidate_below'))}"


def render_action_logic_panel(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    add_forecast = action_forecast_context(state, add_item)
    remove_forecast = action_forecast_context(state, remove_item)
    proxy_score = action_proxy_score(action)
    next_spread = None
    five_spread = None
    if add_forecast and remove_forecast:
        add_next = window_bias_pct(add_forecast, "next_day")
        remove_next = window_bias_pct(remove_forecast, "next_day")
        add_five = window_bias_pct(add_forecast, "five_day")
        remove_five = window_bias_pct(remove_forecast, "five_day")
        if add_next is not None and remove_next is not None:
            next_spread = add_next - remove_next
        if add_five is not None and remove_five is not None:
            five_spread = add_five - remove_five
    trade_amount = as_float(action.get("trade_amount"))
    model_effect = trade_amount * five_spread / 100 if trade_amount is not None and five_spread is not None else None
    rows = [
        [
            "为什么要做",
            "；".join(business_text(item) for item in (action.get("rationale") or [])) or business_text(action.get("summary") or "-"),
        ],
        [
            "相比不调仓的好处",
            (
                f"把 {code_label((remove_item or {}).get('primary_pool')) or '原参照腿'} 的修复/等待口径，"
                f"替换为 {code_label((add_item or subject_item or {}).get('primary_pool'))} 的主线/候选口径；"
                f"同时把资金、研究和趋势证据集中到更强的一侧。"
                if add_item and remove_item
                else "保持当前对象在复核清单中，先避免无证据加仓。"
            ),
        ],
        [
            "预期收益如何变化",
            (
                f"当前没有正式目标价收益预测；用结构改善代理分 {fmt_number(proxy_score)} 和短周期模型做参照。"
                f"下一交易日中值偏置差 {fmt_bias_delta(next_spread)}，5日中值偏置差 {fmt_bias_delta(five_spread)}"
                f"{f'，按 {fmt_money_cn(trade_amount)} 试单折算约 {fmt_money_cn(model_effect)} 的模型弹性' if model_effect is not None else ''}。"
                "该口径不是收益承诺。"
            ),
        ],
        [
            "目标价口径",
            action_target_price_text(add_item or subject_item, detail_context_for_symbol(state, (add_item or subject_item or {}).get("ts_code"))),
        ],
    ]
    return (
        "<section class='panel'>"
        "<h2>完整操作逻辑</h2>"
        "<div class='section-intro'>这块把结论背后的“为什么、好处、收益口径和目标价缺口”直接摊开；不能给确定答案的地方会明确标成缺口。</div>"
        f"{render_html_table(['问题', '系统当前回答'], [[escape(a), escape(b)] for a, b in rows], '当前没有可展示的操作逻辑。')}"
        "</section>"
    )


def render_action_execution_panel(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    active_item = add_item or subject_item
    active_forecast = action_forecast_context(state, active_item)
    active_context = detail_context_for_symbol(state, (active_item or {}).get("ts_code"))
    target_text = action_target_price_text(active_item, active_context)
    next_checks = [business_text(item) for item in (action.get("next_checks") or [])]
    if active_item:
        next_checks.extend(business_text(item) for item in (active_item.get("next_check_items") or [])[:3])
    exit_rules = []
    if active_item:
        exit_rules.append(f"跌破或确认失效：{paper_watch_line(state, active_item.get('ts_code'))}")
        if active_forecast.get("ma_20") not in (None, ""):
            exit_rules.append(f"若重新跌回 MA20（{fmt_number(active_forecast.get('ma_20'))}）且量能不能修复，降级或卖出。")
        exit_rules.append("若最新公告、电话会或研报证伪核心 thesis，停止加仓并重新评估。")
        exit_rules.append("若出现 critical 风险预警，优先执行风控而不是继续按原计划推进。")
    if remove_item:
        exit_rules.append(f"若调出腿 {remove_item.get('name') or remove_item.get('ts_code')} 重新站上关键均线且研究/管理层原话修复，调出理由需要复核。")
    rows = [
        ["执行动作", business_text(action.get("summary") or "-")],
        ["执行规模", f"参照金额 {fmt_money_cn(action.get('trade_amount'))} / 组合占比 {fmt_ratio(action.get('trade_amount_pct'))}"],
        ["参考买价", action_price_line(active_item, active_forecast)],
        ["短周期区间", f"下一交易日 {fmt_forecast_window(active_forecast.get('next_day'))}；5日 {fmt_forecast_window(active_forecast.get('five_day'))}"],
        ["买后重点", "；".join(item for item in next_checks if item) or "-"],
        ["什么情况下卖出/降级", "；".join(exit_rules) or "-"],
        ["目标价", target_text],
    ]
    return (
        "<section class='panel'>"
        "<h2>执行与卖出规则</h2>"
        "<div class='section-intro'>这块只回答“怎么做、按什么价位看、买后盯什么、什么情况下撤”。</div>"
        f"{render_html_table(['事项', '口径'], [[escape(a), escape(b)] for a, b in rows], '当前没有执行规则。')}"
        "</section>"
    )


def render_action_evidence_panel(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    rows: list[list[str]] = []

    def add_row(layer: str, conclusion: str, evidence: str, rel_path: str | None = None) -> None:
        rows.append(
            [
                escape(layer),
                escape(conclusion),
                escape(evidence),
                link_for_rel_path(rel_path, "查看原文") if rel_path else "<span class='muted'>暂无原文</span>",
            ]
        )

    plan_rel = ((state.get("rotation") or {}).get("execution_plan_artifact") or {}).get("rel_path") or ((state.get("portfolio_action") or {}).get("artifact") or {}).get("rel_path")
    add_row("组合执行计划", "门禁已通过，允许进入受控试单前检查。", f"动作阶段 {code_label(action.get('gate_status'))}；参照金额 {fmt_money_cn(action.get('trade_amount'))}；结构改善代理分 {fmt_number(action_proxy_score(action))}", plan_rel)

    for role, item in (("调入腿", add_item), ("调出腿", remove_item), ("复核对象", subject_item)):
        if not item:
            continue
        context = detail_context_for_symbol(state, item.get("ts_code"))
        forecast = context.get("forecast") or {}
        official = context.get("official_material") or item
        external = context.get("external_research") or item
        transcript = context.get("public_transcript") or item
        add_row(
            f"{role} / 趋势价格",
            business_text(item.get("trend_summary") or "-"),
            action_price_line(item, forecast),
            forecast.get("event_source_rel_path"),
        )
        add_row(
            f"{role} / 官方一手",
            code_label(official_material_freshness(official)),
            official_material_summary(official),
            (official_material_source_rel_paths(official) or [None])[0],
        )
        add_row(
            f"{role} / 外部研报",
            external_research_fact(item, context),
            action_target_price_text(item, context),
            external.get("source_rel_path") or item.get("external_research_source_rel_path"),
        )
        add_row(
            f"{role} / 管理层原话",
            code_label((transcript or {}).get("freshness_label") or item.get("public_transcript_freshness")),
            public_transcript_summary(transcript or item),
            public_transcript_source_rel_path(transcript or item),
        )
        add_row(
            f"{role} / 资金面",
            "资金参与度与持仓锚点",
            capital_flow_fact(context),
            None,
        )
    return (
        "<section class='panel'>"
        "<h2>证据链</h2>"
        "<div class='section-intro'>每条结论都挂到可复核事实：组合计划、趋势价格、官方一手、外部研报/机构观点、管理层原话和资金面。</div>"
        f"{render_html_table(['证据层', '结论', '事实依据', '原文'], rows, '当前没有证据链。')}"
        "</section>"
    )


def render_action_capability_gap_panel(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    gaps = []
    for role, item in (("调入腿", add_item), ("调出腿", remove_item), ("复核对象", subject_item)):
        if not item:
            continue
        context = detail_context_for_symbol(state, item.get("ts_code"))
        external = context.get("external_research") or {}
        official = context.get("official_material") or {}
        if (external.get("target_price_yuan") or item.get("target_price_yuan")) in (None, ""):
            gaps.append(f"{role} {item.get('name') or item.get('ts_code')} 缺统一目标价。")
        if not context.get("public_transcript") and not item.get("public_transcript_summary"):
            gaps.append(f"{role} {item.get('name') or item.get('ts_code')} 缺可用电话会/管理层原话。")
        if official and official.get("freshness_label") in {"missing", "stale"}:
            gaps.append(f"{role} {item.get('name') or item.get('ts_code')} 官方一手材料不够新。")
    if not gaps:
        return ""
    items = "".join(f"<li>{escape(gap)}</li>" for gap in gaps)
    return (
        "<section class='panel'>"
        "<h2>能力和证据缺口</h2>"
        "<div class='section-intro'>这些缺口会限制动作强度：有缺口时只能受控试单或复核，不能升级成无条件买入。</div>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def pct_from_fraction(value: object) -> str:
    number = as_float(value)
    if number is None:
        return "-"
    return f"{number * 100:+.2f}%"


def clean_report_sentence(text: str | None) -> str:
    cleaned = business_text(text)
    cleaned = cleaned.replace("thesis（投资逻辑）", "投资逻辑").replace("thesis", "投资逻辑")
    cleaned = cleaned.replace("和 投资逻辑", "和投资逻辑")
    cleaned = cleaned.replace("critical 风险预警", "最高级风险预警")

    def money_repl(match: re.Match[str]) -> str:
        return f"拟替换金额约 {fmt_money_cn(match.group(1))}"

    return re.sub(r"拟替换金额约\s*([0-9]+(?:\.[0-9]+)?)", money_repl, cleaned)


def find_strategy_evidence(state: dict, ts_code: str | None) -> dict | None:
    if not ts_code:
        return None
    for item in (((state.get("opportunity_engine") or {}).get("evidence") or {}).get("items") or []):
        if item.get("ts_code") == ts_code:
            return item
    return None


def external_model_sentence(context: dict | None) -> str:
    external = (context or {}).get("external_research") or {}
    if not external:
        return "当前没有可用的外部研报模型。"
    parts = []
    for label, key in (("收入", "revenue_billion"), ("净利润", "net_profit_billion"), ("EPS", "eps_yuan"), ("PE", "pe_multiple")):
        series = external.get(key) or {}
        if len(series) >= 2:
            keys = sorted(series.keys())
            parts.append(f"{label} {keys[0]} {fmt_number(series.get(keys[0]))} -> {keys[-1]} {fmt_number(series.get(keys[-1]))}")
        elif len(series) == 1:
            only_key = next(iter(series))
            parts.append(f"{label} {only_key} {fmt_number(series.get(only_key))}")
    return "；".join(parts) if parts else external_research_summary(external)


def external_research_items(context: dict | None) -> list[dict]:
    items = list((context or {}).get("external_research_items") or [])
    if not items and (context or {}).get("external_research"):
        items = [(context or {}).get("external_research") or {}]
    return [item for item in items if item]


def research_orgs(items: list[dict]) -> list[str]:
    orgs = []
    seen = set()
    for item in items:
        org = str(item.get("org_name") or "").strip()
        if not org or org in seen:
            continue
        seen.add(org)
        orgs.append(org)
    return orgs


def metric_range_sentence(items: list[dict], key: str, label: str) -> str | None:
    by_year: dict[str, list[float]] = {}
    for item in items:
        for year, value in (item.get(key) or {}).items():
            number = as_float(value)
            if number is None:
                continue
            by_year.setdefault(str(year), []).append(number)
    if not by_year:
        return None
    year = sorted(by_year.keys())[0]
    values = by_year[year]
    if not values:
        return None
    low = min(values)
    high = max(values)
    if abs(high - low) < 1e-9:
        return f"{label} {year} {fmt_number(low)}"
    return f"{label} {year} 区间 {fmt_number(low)} - {fmt_number(high)}"


def target_price_range_sentence(items: list[dict]) -> str | None:
    values = [as_float(item.get("target_price_yuan")) for item in items]
    values = [value for value in values if value is not None]
    if not values:
        return None
    low = min(values)
    high = max(values)
    if abs(high - low) < 1e-9:
        return f"目标价样本 {fmt_number(low)}"
    return f"目标价样本区间 {fmt_number(low)} - {fmt_number(high)}"


def research_source_profile(context: dict | None, item: dict | None) -> dict:
    items = external_research_items(context)
    official = (context or {}).get("official_material") or {}
    transcript = (context or {}).get("public_transcript") or {}
    official_count = len(official.get("items") or []) or int(official.get("item_count") or 0)
    transcript_freshness = str(transcript.get("freshness_label") or (item or {}).get("public_transcript_freshness") or "missing")
    orgs = research_orgs(items)
    score = 0
    if len(items) >= 3 and len(orgs) >= 2:
        score += 2
    elif len(items) >= 2:
        score += 1
    if official_count >= 2:
        score += 2
    elif official_count == 1:
        score += 1
    if transcript_freshness in {"fresh", "usable"}:
        score += 1
    if score >= 4:
        grade = "可形成研究判断"
    elif score >= 2:
        grade = "中等置信假设"
    else:
        grade = "素材型假设"
    return {
        "grade": grade,
        "research_count": len(items),
        "org_count": len(orgs),
        "orgs": orgs,
        "official_count": official_count,
        "transcript_freshness": transcript_freshness,
    }


def research_profile_sentence(profile: dict) -> str:
    org_text = "、".join(profile.get("orgs") or []) or "0家"
    return (
        f"证据等级：{profile.get('grade')}。"
        f"当前已接入结构化卖方研报 {profile.get('research_count') or 0} 篇 / {profile.get('org_count') or 0} 家（{org_text}），"
        f"官方一手材料 {profile.get('official_count') or 0} 条，"
        f"电话会原话状态为{code_label(profile.get('transcript_freshness'))}。"
    )


def clean_research_title(title: str | None) -> str:
    text = plain_text(title)
    text = re.sub(r"^[0-9A-Z.]+\.?[A-Z]*\s+", "", text)
    text = text.replace("东方财富研报表格结构化", "").replace("东方财富研报结构化", "")
    text = re.sub(r"\s+", " ", text).strip(" ：:-")
    return text or plain_text(title)


def research_consensus_sentence(context: dict | None) -> str:
    items = external_research_items(context)
    if not items:
        return "当前还没有结构化研报样本，不能形成卖方共识或分歧判断。"
    titles = [compact_text(clean_research_title(item.get("title")), 58) for item in items[:3] if item.get("title")]
    ratings = sorted({str(item.get("rating_name")) for item in items if item.get("rating_name")})
    model_parts = [
        item
        for item in [
            metric_range_sentence(items, "revenue_billion", "收入"),
            metric_range_sentence(items, "net_profit_billion", "净利润"),
            metric_range_sentence(items, "eps_yuan", "EPS"),
            metric_range_sentence(items, "pe_multiple", "PE"),
            target_price_range_sentence(items),
        ]
        if item
    ]
    pieces = [
        f"已读研报主题集中在：{'；'.join(titles) if titles else '暂无标题主题'}。",
        f"评级口径：{'、'.join(ratings) if ratings else '暂无评级'}。",
    ]
    if model_parts:
        pieces.append(f"模型可比项：{'；'.join(model_parts[:4])}。")
    return "".join(pieces)


def research_gap_sentence(profile: dict, name: str) -> str:
    gaps = []
    if (profile.get("research_count") or 0) < 3:
        gaps.append(f"{name}还需要至少 3 篇卖方或独立研究样本")
    if (profile.get("org_count") or 0) < 2:
        gaps.append(f"{name}还需要至少 2 家以上机构来源")
    if (profile.get("official_count") or 0) <= 0:
        gaps.append(f"{name}缺官方一手材料，不能只靠研报转述")
    if profile.get("transcript_freshness") not in {"fresh", "usable"}:
        gaps.append(f"{name}缺近期电话会/管理层原话，需要补订单、指引、毛利率、客户和产能表述")
    gaps.append("还需要补行业层数据，如需求增速、价格/份额变化、客户 capex、库存和竞争格局，用来交叉验证公司逻辑")
    return "；".join(gaps)


def render_fundamental_synthesis_block(title: str, name: str, context: dict, item: dict | None, role: str) -> str:
    profile = research_source_profile(context, item)
    consensus = research_consensus_sentence(context)
    gap_text = research_gap_sentence(profile, name)
    role_text = (
        "调入腿现在只能被视为研究假设：需要证明它的收入、利润或估值驱动确实优于市场预期。"
        if role == "add"
        else "调出腿现在只能被视为机会成本判断：需要证明它的业务动能、预期修复或性价比弱于调入腿。"
    )
    return (
        "<div class='report-block'>"
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(research_profile_sentence(profile))}{escape(role_text)}</p>"
        f"<p>{escape(consensus)}这些材料只能说明“市场正在如何叙事和建模”，不能直接替代系统自己的结论。</p>"
        f"<p class='report-warning'>升级为高质量二级市场研报前必须补齐：{escape(gap_text)}</p>"
        "</div>"
    )


def action_research_source_link(context: dict | None, label: str = "查看研报原文") -> str:
    external = (context or {}).get("external_research") or {}
    return link_for_rel_path(external.get("source_rel_path"), label) if external.get("source_rel_path") else "<span class='muted'>暂无研报原文</span>"


def action_official_source_link(context: dict | None, label: str = "查看官方材料") -> str:
    official = (context or {}).get("official_material") or {}
    paths = official_material_source_rel_paths(official)
    return link_for_rel_path(paths[0], label) if paths else "<span class='muted'>暂无官方原文</span>"


def signal_sentence(item: dict | None, forecast: dict | None) -> str:
    item = item or {}
    forecast = forecast or {}
    close = as_float(item.get("latest_close") or forecast.get("latest_close"))
    ma20 = as_float(forecast.get("ma_20"))
    ma60 = as_float(forecast.get("ma_60"))
    rsi = as_float(forecast.get("rsi_14"))
    pieces = [action_price_line(item, forecast)]
    if close is not None and ma20 is not None and ma60 is not None:
        if close > ma20 > ma60:
            pieces.append("价格在 MA20 与 MA60 上方，且 MA20 高于 MA60，属于趋势延续形态。")
        elif close < ma20:
            pieces.append("价格低于 MA20，说明短线结构仍在修复或转弱区。")
        else:
            pieces.append("价格处在关键均线之间，趋势结论需要继续确认。")
    if rsi is not None and rsi >= 78:
        pieces.append(f"RSI {fmt_number(rsi)} 已进入短线过热区，买入只能用受控试单。")
    return " ".join(pieces)


def strategy_evidence_sentence(evidence_item: dict | None) -> str:
    if not evidence_item:
        return "当前没有接入同一套策略回测证据，不能用历史胜率支持这条腿。"
    best = evidence_item.get("best_evidence") or {}
    if not best:
        return "当前没有形成有效的策略证据。"
    return (
        f"最佳策略为“{code_label(best.get('strategy_id'))}”，样本 {fmt_number(best.get('trade_count') or 0)} 笔，"
        f"持有 {fmt_number(best.get('hold_days') or 0)} 个交易日；胜率 {pct_from_fraction(best.get('win_rate'))}，"
        f"平均收益 {pct_from_fraction(best.get('avg_return'))}，中位数收益 {pct_from_fraction(best.get('median_return'))}，"
        f"最差收益 {pct_from_fraction(best.get('worst_return'))}，证据标签为{code_label(best.get('evidence_label'))}。"
    )


def render_strategy_samples(evidence_item: dict | None) -> str:
    best = (evidence_item or {}).get("best_evidence") or {}
    samples = best.get("sample_trades") or []
    if not samples:
        return "<p class='report-muted'>当前没有可展示的历史样本明细。</p>"
    rows = []
    for sample in samples[-5:]:
        rows.append(
            "<li>"
            f"{escape(sample.get('entry_date') or '-')} -> {escape(sample.get('exit_date') or '-')}："
            f"{escape(pct_from_fraction(sample.get('return')))}；{escape(sample.get('signal_note') or '-')}"
            "</li>"
        )
    return "<ul>" + "".join(rows) + "</ul>"


def investment_artifacts_for_action(state: dict, action: dict) -> dict:
    action_id = action.get("action_id")
    return ((state.get("portfolio_action") or {}).get("investment_artifacts") or {}).get(action_id) or {}


def investment_snapshot_payload(snapshot: dict | None) -> dict:
    return (snapshot or {}).get("payload") or {}


def investment_report_rel_path_for_action(state: dict, action: dict) -> str | None:
    artifacts = investment_artifacts_for_action(state, action)
    report_snapshot = artifacts.get("investment_report_snapshot") or {}
    report_payload = investment_snapshot_payload(report_snapshot)
    return report_payload.get("report_md_rel_path") or report_payload.get("model_response_text_rel_path")


def read_project_text(rel_path: str | None) -> str | None:
    path = resolve_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def model_output_body(text: str | None) -> str:
    raw = str(text or "").strip()
    marker = "\n## Model Output\n"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    marker = "## Model Output"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    return raw


def normalize_markdown_heading(title: str) -> str:
    text = re.sub(r"^\s*#+\s*", "", str(title or "")).strip()
    text = re.sub(r"^[0-9一二三四五六七八九十]+[.、．]\s*", "", text)
    return re.sub(r"\s+", "", text).lower()


def extract_markdown_section(text: str | None, titles: list[str]) -> str | None:
    body = model_output_body(text)
    if not body:
        return None
    wanted = {normalize_markdown_heading(title) for title in titles}
    lines = body.splitlines()
    start = None
    start_level = None
    for index, line in enumerate(lines):
        match = re.match(r"^(#{2,5})\s+(.+?)\s*$", line)
        if not match:
            continue
        if normalize_markdown_heading(match.group(2)) in wanted:
            start = index
            start_level = len(match.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{2,5})\s+(.+?)\s*$", lines[index])
        if match and len(match.group(1)) <= (start_level or 2):
            end = index
            break
    section = "\n".join(lines[start:end]).strip()
    section_lines = section.splitlines()
    if section_lines and re.match(r"^#{2,5}\s+", section_lines[0]):
        section = "\n".join(section_lines[1:]).strip()
    return section or None


def render_report_markdown_section(title: str, content: str | None, empty_text: str) -> str:
    if not content:
        return (
            "<section class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</section>"
        )
    return (
        "<section class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"{render_markdown_block(content)}"
        "</section>"
    )


def render_report_driven_action_sections(state: dict, action: dict) -> str:
    report_rel_path = investment_report_rel_path_for_action(state, action)
    report_text = read_project_text(report_rel_path)
    if not report_text:
        return ""
    operation = extract_markdown_section(report_text, ["调仓操作"])
    operation_plan = extract_markdown_section(report_text, ["操作计划"])
    risk = extract_markdown_section(report_text, ["风险与证伪"])
    logic = extract_markdown_section(report_text, ["逻辑分析"])
    consensus = extract_markdown_section(report_text, ["共识与分歧"])
    technical = extract_markdown_section(report_text, ["技术分析"])

    operation_parts = [part for part in (operation, operation_plan, risk) if part]
    logic_parts = [part for part in (logic, consensus) if part]
    operation_text = "\n\n".join(operation_parts)
    logic_text = "\n\n".join(logic_parts)
    return (
        f"{render_report_markdown_section('调仓操作', operation_text, '报告中暂未抽取到调仓操作段落。')}"
        f"{render_report_markdown_section('逻辑分析', logic_text, '报告中暂未抽取到逻辑分析段落。')}"
        f"{render_report_markdown_section('技术分析', technical, '报告中暂未抽取到技术分析段落。')}"
    )


def compact_summary_value(value) -> str:
    if value in (None, "", [], {}):
        return "-"
    if isinstance(value, list):
        return "；".join(compact_summary_value(item) for item in value if item not in (None, "", [], {}))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item in (None, "", [], {}):
                continue
            parts.append(f"{code_label(key)}：{compact_summary_value(item)}")
        return "；".join(parts) if parts else "-"
    return business_text(str(value))


def render_dashboard_summary_action_plan(summary: dict) -> str:
    plan = summary.get("portfolio_action_plan")
    if not isinstance(plan, dict) or not plan:
        return "<div class='empty'>当前报告还没有结构化操作计划。</div>"
    initial_action = plan.get("initial_action")
    if isinstance(initial_action, dict):
        action_rows = []
        for key, label in (("buy", "调入候选"), ("sell", "调出候选")):
            item = initial_action.get(key)
            if not isinstance(item, dict):
                continue
            conditions = item.get("conditions") or []
            if isinstance(conditions, list):
                condition_text = "；".join(str(condition) for condition in conditions if condition not in (None, ""))
            else:
                condition_text = str(conditions or "-")
            action_rows.append(
                [
                    escape(label),
                    escape(compact_summary_value(item.get("ticker") or item.get("name"))),
                    escape(fmt_money_cn(item.get("amount_cny")) if item.get("amount_cny") not in (None, "") else "-"),
                    escape(condition_text or "-"),
                ]
            )
        condition_labels = {
            "add_conditions": "提高敞口条件",
            "reduce_conditions": "降低敞口条件",
            "exit_conditions": "退出观察条件",
            "hold_conditions": "继续观察条件",
        }
        condition_rows = []
        for key, label in condition_labels.items():
            value = plan.get(key)
            if value in (None, "", [], {}):
                continue
            condition_rows.append([escape(label), escape(compact_summary_value(value))])
        body = render_html_table(["动作", "标的", "候选金额", "前置条件"], action_rows, "当前没有操作步骤。")
        if condition_rows:
            body += "<div style='height:10px'></div>" + render_html_table(["条件", "处理"], condition_rows, "当前没有触发条件。")
        return body

    preferred_order = [
        "initial",
        "initial_build",
        "initial_action",
        "add",
        "add_position",
        "reduce",
        "reduce_exposure",
        "reduce_position",
        "exit",
        "exit_observation",
        "stop_loss",
        "hold",
        "watch",
    ]
    ordered_keys = [key for key in preferred_order if key in plan]
    ordered_keys.extend(key for key in plan.keys() if key not in set(ordered_keys))
    steps = []
    conditions = []
    for key in ordered_keys:
        value = plan.get(key)
        label = code_label(key)
        text = compact_summary_value(value)
        if key.startswith("step"):
            steps.append([escape(label), escape(text)])
        elif "condition" in key or "trigger" in key:
            conditions.append([escape(label), escape(text)])
        else:
            steps.append([escape(label), escape(text)])
    body = ""
    if steps:
        body += render_html_table(["步骤", "动作"], steps, "当前没有操作步骤。")
    if conditions:
        body += "<div style='height:10px'></div>" + render_html_table(["条件", "处理"], conditions, "当前没有触发条件。")
    return body


def render_dashboard_summary_kill_triggers(summary: dict) -> str:
    triggers = summary.get("kill_triggers")
    if not isinstance(triggers, list) or not triggers:
        return "<div class='empty'>当前报告还没有结构化证伪触发器。</div>"
    rows = []
    for item in triggers[:8]:
        if isinstance(item, dict):
            condition = (
                item.get("condition")
                or item.get("trigger")
                or item.get("name")
                or item.get("title")
                or compact_summary_value(item)
            )
            verification = (
                item.get("verification")
                or item.get("verify_method")
                or item.get("source")
                or item.get("action")
                or "触发后暂停加仓并复核仓位"
            )
            impact = (
                item.get("impact")
                or item.get("thesis_effect")
                or item.get("reason")
                or item.get("priority")
                or "重新评估调仓结论"
            )
            rows.append(
                [
                    escape(compact_summary_value(condition)),
                    escape(compact_summary_value(verification)),
                    escape(compact_summary_value(impact)),
                ]
            )
        else:
            rows.append([escape(compact_summary_value(item)), "触发后暂停加仓并复核仓位", "重新评估调仓结论"])
    return render_html_table(["触发器", "验证/处理", "影响"], rows, "当前没有证伪触发器。")


def render_dashboard_summary_followups(summary: dict) -> str:
    tasks = summary.get("follow_up_tasks")
    if not isinstance(tasks, list) or not tasks:
        return "<div class='empty'>当前报告还没有后续跟踪任务。</div>"
    if any(isinstance(item, dict) for item in tasks):
        rows = []
        for item in tasks[:8]:
            if isinstance(item, dict):
                rows.append(
                    [
                        escape(compact_summary_value(item.get("priority"))),
                        escape(compact_summary_value(item.get("task") or item.get("research_question"))),
                        escape(compact_summary_value(item.get("deadline") or item.get("frequency"))),
                    ]
                )
            else:
                rows.append(["-", escape(compact_summary_value(item)), "-"])
        return render_html_table(["优先级", "任务", "时间/频率"], rows, "当前没有后续跟踪任务。")
    items = "".join(f"<li>{escape(compact_summary_value(item))}</li>" for item in tasks[:8])
    return f"<ul>{items}</ul>"


def render_source_discipline_audit(audit: dict | None) -> str:
    audit = audit or {}
    status = audit.get("status") or "unknown"
    findings = audit.get("findings") or []
    if status == "pass":
        return "<p class='muted'>来源纪律审计：当前没有发现需要单独提示的无来源关键变量。</p>"
    rows = []
    for item in findings[:8]:
        rows.append(
            [
                escape(item.get("label") or item.get("term_id") or "-"),
                escape(item.get("message") or "-"),
            ]
        )
    notes = "".join(f"<li>{escape(item)}</li>" for item in (audit.get("missing_source_notes") or [])[:5])
    return (
        "<div class='report-warning'>关键变量仍缺少一手或硬数据锚点，需要先补证再升级置信度。</div>"
        f"{render_html_table(['变量', '问题'], rows, '当前没有具体问题。')}"
        f"{'<ul>' + notes + '</ul>' if notes else ''}"
    )


def render_investment_evidence_gap_tasks(task_snapshot: dict | None, fallback_tasks: list[dict] | None = None) -> str:
    payload = investment_snapshot_payload(task_snapshot)
    tasks = payload.get("tasks") or fallback_tasks or []
    if not tasks:
        return "<div class='empty'>当前没有需要单独补证的关键变量。</div>"

    rows = []
    for task in tasks[:8]:
        accepted = task.get("accepted_evidence") or []
        if isinstance(accepted, list):
            accepted_text = "；".join(str(item) for item in accepted[:3])
        else:
            accepted_text = str(accepted)
        rows.append(
            [
                badge(task.get("priority") or "P1", "warning"),
                escape(task.get("variable_label") or task.get("variable_id") or "-"),
                escape(compact_summary_value(task.get("research_question"))),
                escape(compact_summary_value(accepted_text)),
                escape(compact_summary_value(task.get("thesis_effect"))),
            ]
        )
    task_rel_path = payload.get("task_md_rel_path")
    link_html = (
        f"<p class='source-link'>{link_for_rel_path(task_rel_path, '打开补证任务包')}</p>" if task_rel_path else ""
    )
    return (
        "<p>这些不是普通抓取清单，而是会决定调仓结论能否升级置信度的关键变量。</p>"
        f"{render_html_table(['优先级', '变量', '研究问题', '验收标准', '对结论的影响'], rows, '当前没有补证任务。')}"
        f"{link_html}"
    )


def render_investment_evidence_gap_fetch(fetch_snapshot: dict | None) -> str:
    payload = investment_snapshot_payload(fetch_snapshot)
    if not payload:
        return "<div class='empty'>补证任务已生成，但还没有执行资料抓取。</div>"
    outputs = (payload.get("fetch_outputs") or {}).get("outputs") or []
    failures = (payload.get("fetch_outputs") or {}).get("failures") or []
    rows = []
    for item in outputs[:8]:
        source_rel_path = item.get("source_rel_path")
        source_html = link_for_rel_path(source_rel_path, compact_summary_value(item.get("title"))) if source_rel_path else "-"
        rows.append(
            [
                escape(compact_summary_value(item.get("entity_id"))),
                source_html,
                escape(compact_summary_value(item.get("published_at"))),
            ]
        )
    summary_rel_path = payload.get("summary_rel_path")
    summary_link = (
        f"<p class='source-link'>{link_for_rel_path(summary_rel_path, '打开补证执行结果')}</p>"
        if summary_rel_path
        else ""
    )
    intro = (
        f"状态：{code_label(fetch_snapshot.get('status') or payload.get('mode'))}；"
        f"已沉淀来源 {fmt_number(payload.get('source_path_count') or 0)} 条；"
        f"待复核失败 {fmt_number(len(failures))} 条。"
    )
    failure_note = ""
    if failures:
        first_failure = failures[0]
        failure_note = (
            "<p class='report-warning'>"
            f"有来源未抓到：{escape(compact_summary_value(first_failure.get('entity_id') or first_failure.get('target_key')))} / "
            f"{escape(compact_summary_value(first_failure.get('error') or first_failure))}"
            "</p>"
        )
    return (
        f"<p>{escape(intro)}</p>"
        f"{render_html_table(['对象', '来源', '日期'], rows, '还没有可展示的补证来源。')}"
        f"{failure_note}"
        f"{summary_link}"
    )


def render_action_deep_report_panel(state: dict, action: dict) -> str:
    artifacts = investment_artifacts_for_action(state, action)
    report_snapshot = artifacts.get("investment_report_snapshot") or {}
    synthesis_snapshot = artifacts.get("investment_research_synthesis_snapshot") or {}
    evidence_snapshot = artifacts.get("investment_evidence_pack_snapshot") or {}
    task_snapshot = artifacts.get("investment_evidence_gap_task_snapshot") or {}
    fetch_snapshot = artifacts.get("investment_evidence_gap_fetch_snapshot") or {}

    report_payload = investment_snapshot_payload(report_snapshot)
    synthesis_payload = investment_snapshot_payload(synthesis_snapshot)
    evidence_payload = investment_snapshot_payload(evidence_snapshot)
    report_rel_path = report_payload.get("report_md_rel_path") or report_payload.get("model_response_text_rel_path")
    synthesis_rel_path = synthesis_payload.get("synthesis_md_rel_path") or synthesis_payload.get("model_response_text_rel_path")
    evidence_rel_path = evidence_payload.get("pack_md_rel_path")

    if not (report_rel_path or synthesis_rel_path or evidence_rel_path):
        return ""

    dashboard_summary = report_payload.get("dashboard_summary") or {}
    source_audit = report_payload.get("source_discipline_audit") or {}
    evidence_gap_tasks = report_payload.get("evidence_gap_tasks") or dashboard_summary.get("evidence_gap_tasks") or []

    links = []
    if report_rel_path:
        links.append(f"<li>{link_for_rel_path(report_rel_path, '打开完整调仓报告')}</li>")
    if synthesis_rel_path:
        links.append(f"<li>{link_for_rel_path(synthesis_rel_path, '查看研究综合底稿')}</li>")
    if evidence_rel_path:
        links.append(f"<li>{link_for_rel_path(evidence_rel_path, '查看证据包')}</li>")

    report_time = report_snapshot.get("created_at") or synthesis_snapshot.get("created_at") or evidence_snapshot.get("created_at")
    conclusion_note = (
        dashboard_summary.get("confidence_note")
        or dashboard_summary.get("entry_decision")
        or dashboard_summary.get("primary_signal")
        or ""
    )
    report_intro = (
        "这份报告由深度投研 agent 和报告主笔 agent 在候选层生成，用来支持人工复核。"
        "它应该优先回答为什么调、怎么调、错了如何处理。"
    )
    return (
        "<section class='panel'>"
        "<h2>完整调仓报告</h2>"
        f"<div class='section-intro'>{escape(report_intro)}</div>"
        "<div class='report-section'>"
        "<div class='report-block'>"
        "<h3>当前可读结论</h3>"
        f"<p>已经为 <strong>{escape(action.get('title') or action.get('action_id') or '-')}</strong> 生成深度报告候选。"
        f"{'生成时间：' + escape(report_time) + '。' if report_time else ''}</p>"
        f"<p>动作：{escape(compact_summary_value(dashboard_summary.get('action_detail') or dashboard_summary.get('action')))}；置信度：{escape(compact_summary_value(dashboard_summary.get('confidence')))}。</p>"
        f"{'<p>' + escape(compact_summary_value(conclusion_note)) + '</p>' if conclusion_note else ''}"
        "</div>"
        "<div class='report-block'>"
        "<h3>继续查看</h3>"
        f"<ul>{''.join(links)}</ul>"
        "</div>"
        "<div class='report-block'>"
        "<h3>结构化操作计划</h3>"
        f"{render_dashboard_summary_action_plan(dashboard_summary)}"
        "</div>"
        "<div class='report-block'>"
        "<h3>证伪与退出触发器</h3>"
        f"{render_dashboard_summary_kill_triggers(dashboard_summary)}"
        "</div>"
        "<div class='report-block'>"
        "<h3>后续跟踪任务</h3>"
        f"{render_dashboard_summary_followups(dashboard_summary)}"
        "</div>"
        "<div class='report-block'>"
        "<h3>待补硬证据</h3>"
        f"{render_investment_evidence_gap_tasks(task_snapshot, evidence_gap_tasks)}"
        "</div>"
        "<div class='report-block'>"
        "<h3>补证进展</h3>"
        f"{render_investment_evidence_gap_fetch(fetch_snapshot)}"
        "</div>"
        "<div class='report-block'>"
        "<h3>证据缺口说明</h3>"
        f"{render_source_discipline_audit(source_audit)}"
        "</div>"
        "</div>"
        "</section>"
    )


def render_action_operation_report(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    active_item = add_item or subject_item
    active_forecast = action_forecast_context(state, active_item)
    title = action.get("title") or "动作详情"
    add_leg = action.get("add") or {}
    remove_leg = action.get("remove") or {}
    add_name = (add_item or add_leg).get("name") or (add_item or add_leg).get("ts_code") or "-"
    add_code = (add_item or add_leg).get("ts_code") or "-"
    remove_name = (remove_item or remove_leg).get("name") or (remove_item or remove_leg).get("ts_code") or "-"
    remove_code = (remove_item or remove_leg).get("ts_code") or "-"
    add_text = f"{add_name} / {add_code}"
    remove_text = f"{remove_name} / {remove_code}"
    next_checks = [clean_report_sentence(item) for item in (action.get("next_checks") or [])]
    if active_item:
        next_checks.extend(clean_report_sentence(item) for item in (active_item.get("next_check_items") or [])[:2])
    active_context = detail_context_for_symbol(state, (active_item or {}).get("ts_code"))
    target_text = action_target_price_text(active_item, active_context)
    exit_rules = [
        f"跌破或确认失效：{paper_watch_line(state, (active_item or {}).get('ts_code'))}",
        f"目标价/验证区间：{target_text}",
        f"若重新跌回 MA20（{fmt_number(active_forecast.get('ma_20'))}）且量能不能修复，降级或卖出。" if active_forecast.get("ma_20") not in (None, "") else "",
        "若最新公告、电话会或研报证伪核心逻辑，停止加仓并重新评估。",
        "若出现最高级风险预警，先执行风控。",
    ]
    next_check_html = "".join(f"<li>{escape(item)}</li>" for item in next_checks if item) or "<li>-</li>"
    exit_rule_html = "".join(f"<li>{escape(item)}</li>" for item in exit_rules if item) or "<li>-</li>"
    return (
        "<section class='panel'>"
        "<h2>调仓的操作</h2>"
        "<div class='report-section'>"
        "<div class='report-block'>"
        f"<h3>{escape(title)}</h3>"
        f"<p>本次动作是参照层建议，不是自动下单。执行口径是调入 <strong>{escape(add_text)}</strong>，调出 <strong>{escape(remove_text)}</strong>，先按受控试单推进。</p>"
        f"<ul><li>参照金额：{escape(fmt_money_cn(action.get('trade_amount')))}，组合占比：{escape(fmt_ratio(action.get('trade_amount_pct')))}。</li>"
        f"<li>参考买价：{escape(action_price_line(active_item, active_forecast))}。</li>"
        f"<li>短周期参考区间：下一交易日 {escape(fmt_forecast_window(active_forecast.get('next_day')))}；5日 {escape(fmt_forecast_window(active_forecast.get('five_day')))}。</li>"
        f"<li>目标价/验证区间：{escape(target_text)}</li></ul>"
        "</div>"
        "<div class='report-block'>"
        "<h3>执行后怎么盯</h3>"
        f"<ul>{next_check_html}</ul>"
        "</div>"
        "<div class='report-block'>"
        "<h3>什么情况下撤退或降级</h3>"
        f"<ul>{exit_rule_html}</ul>"
        "</div>"
        "</div>"
        "</section>"
    )


def render_action_logic_report(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    add_context = detail_context_for_symbol(state, (add_item or {}).get("ts_code"))
    remove_context = detail_context_for_symbol(state, (remove_item or {}).get("ts_code"))
    add_external = add_context.get("external_research") or {}
    remove_external = remove_context.get("external_research") or {}
    proxy_score = fmt_number(action_proxy_score(action))
    add_name = (add_item or {}).get("name") or "调入标的"
    remove_name = (remove_item or {}).get("name") or "调出标的"
    add_profile = research_source_profile(add_context, add_item)
    remove_profile = research_source_profile(remove_context, remove_item)
    thesis_gap = []
    if not (add_context.get("public_transcript") or (add_item or {}).get("public_transcript_summary")):
        thesis_gap.append(f"{add_name}缺最新电话会/管理层原话抽取")
    if not add_external.get("target_price_yuan"):
        thesis_gap.append(f"{add_name}外部研报没有统一目标价")
    if remove_item and not remove_external:
        thesis_gap.append(f"{remove_name}缺可复核的外部研报模型")
    if add_profile.get("grade") != "可形成研究判断":
        thesis_gap.append(f"{add_name}还没有达到多源交叉验证的研报级证据")
    if remove_item and remove_profile.get("grade") == "素材型假设":
        thesis_gap.append(f"{remove_name}调出理由仍偏素材型，不能写成业务恶化结论")
    thesis_gap_text = "；".join(thesis_gap) if thesis_gap else "未发现关键缺口。"
    return (
        "<section class='panel'>"
        "<h2>逻辑分析</h2>"
        "<div class='report-section'>"
        f"{render_fundamental_synthesis_block(f'调入 {add_name}：研究假设与证据等级', add_name, add_context, add_item, 'add')}"
        f"{render_fundamental_synthesis_block(f'调出 {remove_name}：机会成本与证据等级', remove_name, remove_context, remove_item, 'remove')}"
        "<div class='report-block'>"
        "<h3>本次到底在赌什么</h3>"
        f"<p>结构改善代理分为 {escape(proxy_score)}。本次调仓真正要验证的不是“某篇研报说了什么”，而是：调入腿的产业数据、公司经营数据、管理层原话和价格行为，能否持续强于调出腿。相比不调仓，它提高了组合对更强主线的暴露；代价是如果调出腿随后被新证据修复，组合会损失这部分反弹。</p>"
        f"<p>当前页面已经不把单篇研报当成结论。卖方研报、电话会、公告和新闻只作为原料，最终判断必须来自多源交叉验证、分歧识别和可证伪假设。</p>"
        f"<p class='report-warning'>证据缺口：{escape(thesis_gap_text)}。这些缺口意味着动作只能是受控试单或研究跟踪，不能升级成高置信调仓。</p>"
        "</div>"
        "</div>"
        "</section>"
    )


def render_action_technical_report(state: dict, action: dict, add_item: dict | None, remove_item: dict | None, subject_item: dict | None) -> str:
    add_forecast = action_forecast_context(state, add_item)
    remove_forecast = action_forecast_context(state, remove_item)
    add_evidence = find_strategy_evidence(state, (add_item or {}).get("ts_code"))
    remove_evidence = find_strategy_evidence(state, (remove_item or {}).get("ts_code"))
    return (
        "<section class='panel'>"
        "<h2>技术分析</h2>"
        "<div class='report-section'>"
        "<div class='report-block'>"
        f"<h3>调入腿技术状态：{escape((add_item or {}).get('name') or '-')}</h3>"
        f"<p>{escape(signal_sentence(add_item, add_forecast))}</p>"
        f"<p>历史验证：{escape(strategy_evidence_sentence(add_evidence))}</p>"
        f"{render_strategy_samples(add_evidence)}"
        "</div>"
        "<div class='report-block'>"
        f"<h3>调出腿技术状态：{escape((remove_item or {}).get('name') or '-')}</h3>"
        f"<p>{escape(signal_sentence(remove_item, remove_forecast))}</p>"
        f"<p>历史验证：{escape(strategy_evidence_sentence(remove_evidence))}</p>"
        "</div>"
        "<div class='report-block'>"
        "<h3>技术结论</h3>"
        f"<p>调入腿的技术依据主要来自趋势结构和轻量历史验证；调出腿的技术状态更偏修复/等待。当前技术面支持“先做受控试单并持续观察”，但并不支持无条件追高。</p>"
        f"<p>后续复盘时，重点看：调入腿是否守住观察/失效位、是否继续保持 MA20 上方运行、历史信号对应的持有窗口内是否兑现；若没有兑现，就说明本次调仓赌的是主线延续但没有发生。</p>"
        "</div>"
        "</div>"
        "</section>"
    )


def render_badge_group(parts: list[tuple[str | None, str]]) -> str:
    items = [badge(text, tone) for text, tone in parts if text not in (None, "")]
    if not items:
        return "<span class='muted'>-</span>"
    return "<div class='badge-row'>" + "".join(items) + "</div>"


def focus_tension_text(item: dict) -> str:
    parts = [item.get("valuation_summary"), item.get("research_summary")]
    transcript_freshness = item.get("public_transcript_freshness")
    if transcript_freshness == "missing":
        parts.append("缺少可直接复核的管理层原话")
    elif transcript_freshness == "stale":
        parts.append("管理层原话偏旧")
    if public_signal_label(item) in {"stretched", "cautious"}:
        parts.append(public_signal_summary(item))
    joined = " / ".join(business_text(part) for part in parts if part)
    return joined or "-"


def render_focus_overview_table(title: str, items: list[dict], intro: str, empty_text: str) -> str:
    rows = []
    for item in items:
        rows.append(
            [
                render_watch_name_link(item),
                render_badge_group(
                    [
                        (item.get("priority"), "neutral"),
                        (item.get("objective_view"), "ghost"),
                        (item.get("primary_pool"), "ghost"),
                    ]
                ),
                escape(business_text(item.get("trend_summary") or "-")),
                escape(compact_text(focus_tension_text(item), 90)),
                escape(compact_text(transcript_status_sentence(item), 88)),
                escape(business_text((item.get("next_check_items") or [None])[0] or "-")),
            ]
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{render_html_table(['标的', '当前口径', '为什么现在要看', '当前主要矛盾', '管理层原话', '下一步'], rows, empty_text)}"
        "</article>"
    )


def render_event_family_panel(title: str, intro: str, items: list[dict]) -> str:
    if not items:
        content = "<div class='empty'>当前没有新事件。</div>"
    else:
        cards = []
        for item in items:
            source_rel_path = item.get("source_rel_path")
            source_html = f"<a href='/artifact?path={quote(source_rel_path)}'>查看原文</a>" if source_rel_path else "暂无原文"
            summary_html = (
                f"<div class='muted' style='margin-top:6px'>{escape(business_text(item.get('summary') or '', 96))}</div>"
                if item.get("summary")
                else ""
            )
            cards.append(
                "<article class='story-card'>"
                "<div class='story-meta'>"
                f"{badge(item.get('calendar_kind') or item.get('event_type'), 'ghost')}"
                f"{badge(item.get('importance'), 'neutral')}"
                f"<span class='muted'>{escape(item.get('event_date') or item.get('publish_time') or '-')}</span>"
                "</div>"
                f"<h3 class='story-title'>{escape(replace_code_tokens(item.get('title') or '-'))}</h3>"
                f"<div class='muted'>对象：{escape(item.get('entity_id') or '-')}</div>"
                f"{summary_html}"
                f"<div class='story-footer'>{source_html}</div>"
                "</article>"
            )
        content = "".join(cards)
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        f"{content}"
        "</article>"
    )


def render_artifact_panel(title: str, artifact: dict | None, intro: str | None = None) -> str:
    if not artifact:
        return (
            "<article class='panel'>"
            f"<h2>{escape(title)}</h2>"
            "<div class='empty'>暂无原文。</div>"
            "</article>"
        )
    preview_html = render_markdown_block(artifact.get("preview")) if artifact.get("preview") else ""
    summary_html = (
        f"<div class='section-intro'>{escape(business_text(artifact.get('summary'), 180))}</div>"
        if artifact.get("summary")
        else ""
    )
    intro_html = f"<div class='section-intro'>{escape(intro)}</div>" if intro else ""
    updated_at = artifact.get("updated_at")
    meta_html = f"<div class='muted'>更新时间：{escape(updated_at)}</div>" if updated_at else ""
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"{intro_html}"
        f"<div>{link_for_artifact(artifact)}</div>"
        f"{meta_html}"
        f"{summary_html}"
        f"{preview_html}"
        "</article>"
    )


def render_focus_cards(items: list[dict], empty_text: str) -> str:
    if not items:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    blocks = []
    for item in items:
        watchpoints = "".join(f"<li>{escape(business_text(point))}</li>" for point in (item.get("watchpoints") or [])[:3])
        next_checks = "".join(f"<li>{escape(business_text(point))}</li>" for point in (item.get("next_check_items") or [])[:3])
        source_html = link_for_rel_path(item.get("source_rel_path"), "研究原文") if item.get("source_rel_path") else "暂无单票研究原文"
        official_material_html = official_material_summary(item)
        public_transcript_html = public_transcript_summary(item)
        public_signal_html = public_signal_summary(item)
        blocks.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3><a href='{research_detail_href(item.get('ts_code'))}'>{escape(item.get('name') or '-')}</a></h3><div class='muted'>{escape(item.get('ts_code') or '-')} · {escape(code_label(item.get('sector')))}</div></div>"
            f"<div>{render_badge_group([(item.get('priority'), 'neutral'), (item.get('objective_view'), 'ghost'), (item.get('primary_pool'), 'ghost')])}</div>"
            "</div>"
            f"<p>{escape(business_text(item.get('trend_summary') or '-'))}</p>"
            f"<div class='muted'>主要矛盾：{escape(focus_tension_text(item))}</div>"
            "<div class='split'>"
            f"<div><h4>核心观察点</h4><ul>{watchpoints or '<li>-</li>'}</ul></div>"
            f"<div><h4>下一步检查</h4><ul>{next_checks or '<li>-</li>'}</ul></div>"
            "</div>"
            f"<div class='muted' style='margin-top:12px'>最新日涨跌：{escape(fmt_pct(item.get('latest_pct_chg')))} · 最新交易日：{escape(item.get('latest_trade_date') or '-')}</div>"
            f"<div class='muted' style='margin-top:8px'>官方一手材料：{escape(official_material_html)}</div>"
            f"<div class='muted' style='margin-top:8px'>电话会原话：{escape(compact_text(transcript_status_sentence(item, 88), 108))}</div>"
            f"<div class='muted' style='margin-top:8px'>公开卖方参照：{escape(public_signal_html)}</div>"
            f"<div class='source-link'>{source_html}</div>"
            "</article>"
        )
    return "".join(blocks)


def render_action_cards(actions: list[dict], state: dict, empty_text: str) -> str:
    if not actions:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    blocks = []
    for action in actions:
        add_leg = action.get("add") or {}
        remove_leg = action.get("remove") or {}
        subject = action.get("subject") or {}
        legs_html = ""
        if add_leg or remove_leg:
            legs_html = (
                f"<div class='pair-mark'>调入：{escape(add_leg.get('name') or add_leg.get('ts_code') or '-')} / "
                f"调出：{escape(remove_leg.get('name') or remove_leg.get('ts_code') or '-')}</div>"
            )
        elif subject:
            legs_html = f"<div class='pair-mark'>对象：{escape(subject.get('name') or '-')} / {escape(subject.get('ts_code') or '-')}</div>"
        rationale_items = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("rationale") or [])[:3])
        next_checks = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("next_checks") or [])[:3])
        risk_flags = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("risk_flags") or [])[:3])
        amount_html = ""
        if action.get("trade_amount") is not None:
            amount_html = (
                f"<div class='muted'>参照金额：{escape(fmt_money_cn(action.get('trade_amount')))}"
                f" / 占比：{escape(fmt_ratio(action.get('trade_amount_pct')))}</div>"
            )
        blocks.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3>{render_action_title_link(action)}</h3>{legs_html}</div>"
            f"<div>{render_badge_group([(action.get('priority'), 'neutral'), (action.get('action_type'), 'ghost'), (action.get('gate_status'), 'ghost')])}</div>"
            "</div>"
            f"<p>{escape(business_text(action.get('summary') or '-'))}</p>"
            f"<div class='muted' style='margin-top:8px'>管理层原话：{escape(action_management_quote_brief(state, action))}</div>"
            f"{amount_html}"
            "<div class='split'>"
            f"<div><h4>动作依据</h4><ul>{rationale_items or '<li>-</li>'}</ul></div>"
            f"<div><h4>下一步检查</h4><ul>{next_checks or '<li>-</li>'}</ul></div>"
            "</div>"
            f"<div style='margin-top:14px'><h4>主要风险</h4><ul>{risk_flags or '<li>-</li>'}</ul></div>"
            f"<div class='source-link'><h4>支撑材料</h4>{render_source_list(action.get('source_refs'), '当前没有关联原文。')}</div>"
            "</article>"
        )
    return "".join(blocks)


def render_rotation_pairs(pairs: list[dict], empty_text: str) -> str:
    if not pairs:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    cards = []
    for pair in pairs:
        add_leg = pair.get("add") or {}
        remove_leg = pair.get("remove") or {}
        gains = "".join(f"<li>{escape(business_text(item))}</li>" for item in (pair.get("expected_positive_change") or [])[:3])
        risks = "".join(f"<li>{escape(business_text(item))}</li>" for item in (pair.get("risk_flags") or [])[:3])
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3><a href='{research_detail_href(add_leg.get('ts_code'))}'>{escape(add_leg.get('name') or '-')}</a> 替换 <a href='{research_detail_href(remove_leg.get('ts_code'))}'>{escape(remove_leg.get('name') or '-')}</a></h3>"
            f"<div class='pair-mark'>{escape(add_leg.get('ts_code') or '-')} -> {escape(remove_leg.get('ts_code') or '-')}</div></div>"
            f"<div>{badge(pair.get('fit_label'), 'ghost')}{badge(pair.get('pair_score'), 'neutral')}</div>"
            "</div>"
            f"<div class='muted' style='margin-bottom:10px'>电话会原话：调入腿 {escape(code_label(add_leg.get('public_transcript_freshness')))} / 调出腿 {escape(code_label(remove_leg.get('public_transcript_freshness')))}</div>"
            "<div class='split'>"
            f"<div><h4>预期正向变化</h4><ul>{gains or '<li>-</li>'}</ul></div>"
            f"<div><h4>主要风险</h4><ul>{risks or '<li>-</li>'}</ul></div>"
            "</div>"
            "</article>"
        )
    return "".join(cards)


def render_watch_table(title: str, items: list[dict], intro: str) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{render_watch_name_link(item)}</td>"
            f"<td>{render_badge_group([(item.get('primary_pool'), 'ghost'), (item.get('objective_view'), 'ghost')])}</td>"
            f"<td>{escape(fmt_pct(item.get('latest_pct_chg')))}</td>"
            f"<td>{escape(business_text(item.get('trend_summary') or '-'))}</td>"
            f"<td>{escape(compact_text(focus_tension_text(item), 88))}</td>"
            f"<td>{escape(compact_text(public_transcript_summary(item), 88))}</td>"
            f"<td>{escape(compact_text(public_signal_summary(item), 88))}</td>"
            "</tr>"
        )
    body = "".join(rows) or "<tr><td colspan='7' class='empty'>暂无数据</td></tr>"
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        f"<div class='section-intro'>{escape(intro)}</div>"
        "<table>"
        "<thead><tr><th>标的</th><th>当前口径</th><th>日涨跌</th><th>当前判断</th><th>主要矛盾</th><th>电话会原话</th><th>公开卖方参照</th></tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
        "</article>"
    )


def render_market_flow_anomaly_table(title: str, items: list[dict], state: dict, empty_text: str) -> str:
    rows = []
    for index, item in enumerate(items or [], start=1):
        ts_code = item.get("ts_code") or item.get("symbol")
        name = item.get("name") or ts_code or "-"
        subject_html = (
            f"{render_rank_badge(index)}"
            f"<div style='display:inline-block; margin-left:10px'>"
            f"<strong>{escape(name)}</strong>"
            f"<div class='muted'>{escape(ts_code or '-')} · {escape(code_label(item.get('market_label') or item.get('market')))}</div>"
            "</div>"
        )
        if find_watch_item(state, ts_code):
            subject_html = (
                f"{render_rank_badge(index)}"
                f"<div style='display:inline-block; margin-left:10px'>"
                f"<strong><a href='{research_detail_href(ts_code)}'>{escape(name)}</a></strong>"
                f"<div class='muted'>{escape(ts_code or '-')} · {escape(code_label(item.get('market_label') or item.get('market')))}</div>"
                "</div>"
            )
        news_html = escape(compact_text(business_text(item.get("news_summary") or "-"), 88))
        if item.get("latest_event_rel_path"):
            news_html += f"<div class='muted'>{link_for_rel_path(item.get('latest_event_rel_path'), '查看原文')}</div>"
        rows.append(
            [
                subject_html,
                escape(item.get("trade_date") or "-"),
                escape(fmt_pct(item.get("pct_chg"))),
                escape(fmt_number(item.get("flow_signal_score"))),
                escape(f"{item.get('volume_ratio_20d'):.2f}x" if item.get("volume_ratio_20d") not in (None, "") else "-"),
                escape(compact_text(business_text(item.get("reason_summary") or "-"), 72)),
                news_html,
            ]
        )
    return (
        "<article class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>这里只展示当前系统已覆盖库里的异动榜单，不把未覆盖的全市场股票硬说成已经扫过。</div>"
        f"{render_html_table(['标的', '交易日', '日涨跌', '异动分数', '量能倍数', '异动原因', '最新资讯'], rows, empty_text)}"
        "</article>"
    )


def fmt_forecast_window(window: dict | None) -> str:
    snapshot = window or {}
    low = snapshot.get("low")
    high = snapshot.get("high")
    mid = snapshot.get("mid")
    bias = snapshot.get("bias_pct")
    width = snapshot.get("range_width_pct")
    if low in (None, "") and high in (None, ""):
        return "-"
    parts = [f"{fmt_number(low)} - {fmt_number(high)}"]
    if mid not in (None, ""):
        parts.append(f"中枢 {fmt_number(mid)}")
    if bias not in (None, ""):
        parts.append(f"偏置 {fmt_pct(bias)}")
    if width not in (None, ""):
        parts.append(f"带宽 {fmt_pct(width)}")
    return " / ".join(parts)


def forecast_driver_summary(item: dict | None, limit: int = 120) -> str:
    snapshot = item or {}
    drivers = [business_text(row) for row in (snapshot.get("driver_lines") or []) if row]
    if not drivers:
        if snapshot.get("description"):
            return business_text(snapshot.get("description"), limit=limit)
        return "当前还没有提取到足够明确的方向驱动。"
    return compact_text("；".join(drivers), limit)


def render_analysis_subject(item: dict, state: dict) -> str:
    ts_code = item.get("ts_code")
    name = item.get("name") or ts_code or item.get("proxy_id") or "-"
    meta_parts = []
    if ts_code:
        meta_parts.append(ts_code)
    if item.get("sector"):
        meta_parts.append(code_label(item.get("sector")))
    if item.get("market_label") or item.get("market"):
        meta_parts.append(code_label(item.get("market_label") or item.get("market")))
    meta_html = f"<div class='muted'>{escape(' · '.join(meta_parts) or '-')}</div>"
    if ts_code and find_watch_item(state, ts_code):
        title_html = f"<a href='{research_detail_href(ts_code)}'><strong>{escape(name)}</strong></a>"
    else:
        title_html = f"<strong>{escape(name)}</strong>"
    return f"{title_html}{meta_html}"


def render_forecast_focus_cards(items: list[dict], state: dict, empty_text: str) -> str:
    if not items:
        return (
            "<section class='panel'>"
            "<h2>重点推演对象</h2>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</section>"
        )
    cards = []
    today = (state.get("overview") or {}).get("today")
    for item in items:
        event_summary = business_text(item.get("event_summary"), 96) or "当前没有足够新的事件锚点。"
        event_recency = fmt_event_recency(item.get("event_published_at"), today=today)
        event_link = (
            link_for_rel_path(item.get("event_source_rel_path"), "查看事件原文")
            if item.get("event_source_rel_path")
            else "暂无可点击原文"
        )
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div>{render_analysis_subject(item, state)}</div>"
            f"<div>{render_badge_group([(item.get('bias_label'), 'neutral'), (item.get('confidence_label'), 'ghost'), (item.get('primary_pool'), 'ghost')])}</div>"
            "</div>"
            f"<p>{escape(forecast_driver_summary(item, 118))}</p>"
            f"<div class='info-grid' style='margin-top:12px'>{render_kv_chips([('最新收盘', item.get('latest_close')), ('日涨跌', fmt_pct(item.get('latest_pct_chg'))), ('20日波动', fmt_pct(item.get('realized_volatility_20d'))), ('趋势强度', item.get('trend_strength')), ('下一交易日', fmt_forecast_window(item.get('next_day'))), ('5日区间', fmt_forecast_window(item.get('five_day')))], chip_class='info-chip compact')}</div>"
            f"<div class='muted' style='margin-top:10px'>行情交易日：{escape(item.get('latest_trade_date') or '-')} · 事件日期：{escape(event_recency)}</div>"
            f"<div class='muted' style='margin-top:8px'>最新事件：{escape(event_summary)}</div>"
            f"<div class='source-link' style='margin-top:8px'>{event_link}</div>"
            "</article>"
        )
    return (
        "<section class='panel'>"
        "<h2>重点推演对象</h2>"
        "<div class='section-intro'>先看最值得先读的几只，快速判断今天谁更像是偏多推进、谁更像需要先防守。</div>"
        f"{''.join(cards)}"
        "</section>"
    )


def render_index_proxy_cards(items: list[dict]) -> str:
    if not items:
        return (
            "<section class='panel'>"
            "<h2>指数代理</h2>"
            "<div class='empty'>当前还没有生成指数代理推演。</div>"
            "</section>"
        )
    cards = []
    for item in items:
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3>{escape(item.get('name') or '-')}</h3><div class='muted'>{escape(code_label(item.get('market_label') or item.get('market')))} · 使用 {escape(fmt_number(item.get('used_member_count') or item.get('member_count') or 0))} 个覆盖标的归一化合成</div></div>"
            f"<div>{render_badge_group([(item.get('bias_label'), 'neutral'), (item.get('confidence_label'), 'ghost')])}</div>"
            "</div>"
            f"<p>{escape(business_text(item.get('description') or ''))}</p>"
            f"<div class='info-grid' style='margin-top:12px'>{render_kv_chips([('最新代理值', item.get('latest_close')), ('下一交易日', fmt_forecast_window(item.get('next_day'))), ('5日区间', fmt_forecast_window(item.get('five_day'))), ('20日波动', fmt_pct(item.get('realized_volatility_20d')))], chip_class='info-chip compact')}</div>"
            "</article>"
        )
    return (
        "<section class='panel'>"
        "<h2>指数代理</h2>"
        "<div class='section-intro'>这里只给覆盖篮子的方向代理，帮助快速判断 A股、港股、美股当前在我们已覆盖样本里的整体偏向。它不是交易所真实指数预测。</div>"
        f"<div class='grid-3'>{''.join(cards)}</div>"
        "</section>"
    )


def render_analysis_forecast_table(title: str, items: list[dict], state: dict, empty_text: str) -> str:
    rows = []
    today = (state.get("overview") or {}).get("today")
    for item in items or []:
        judgment_html = (
            f"{render_badge_group([(item.get('bias_label'), 'neutral'), (item.get('confidence_label'), 'ghost'), (item.get('primary_pool'), 'ghost')])}"
            f"<div class='muted' style='margin-top:6px'>20日波动 {escape(fmt_pct(item.get('realized_volatility_20d')))} / 最新价 {escape(fmt_number(item.get('latest_close')))} / 行情交易日 {escape(item.get('latest_trade_date') or '-')}</div>"
        )
        event_text = business_text(item.get("event_summary"), 82) or "当前没有足够新的事件锚点。"
        event_html = (
            f"<div>{escape(event_text)}</div>"
            f"<div class='muted' style='margin-top:6px'>事件日期：{escape(fmt_event_recency(item.get('event_published_at'), today=today))}</div>"
        )
        if item.get("event_source_rel_path"):
            event_html += f"<div class='muted'>{link_for_rel_path(item.get('event_source_rel_path'), '查看原文')}</div>"
        rows.append(
            [
                render_analysis_subject(item, state),
                judgment_html,
                escape(fmt_forecast_window(item.get("next_day"))),
                escape(fmt_forecast_window(item.get("five_day"))),
                escape(forecast_driver_summary(item, 100)),
                event_html,
            ]
        )
    return (
        "<section class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>先给方向和区间，再说明为什么会这么推。页面默认只按系统当前已覆盖股票展示，不冒充全市场都已建模。</div>"
        f"{render_html_table(['标的', '当前判断', '下一交易日区间', '5日区间', '为什么这么推', '最新事件'], rows, empty_text)}"
        "</section>"
    )


def render_symbol_forecast_panel(forecast: dict | None) -> str:
    snapshot = forecast or {}
    if not snapshot:
        return (
            "<article class='panel'>"
            "<h2>价格区间推演</h2>"
            "<div class='empty'>当前还没有这只标的的区间推演结果。</div>"
            "</article>"
        )
    event_summary = business_text(snapshot.get("event_summary"), 92) or "当前没有足够新的事件锚点。"
    event_recency = fmt_event_recency(snapshot.get("event_published_at"))
    event_link = (
        link_for_rel_path(snapshot.get("event_source_rel_path"), "查看事件原文")
        if snapshot.get("event_source_rel_path")
        else "暂无可点击原文"
    )
    return (
        "<article class='panel'>"
        "<h2>价格区间推演</h2>"
        "<div class='section-intro'>这层只回答短周期里更像偏多、震荡还是偏空，以及下一交易日和 5 日大致可能运行在哪个区间。</div>"
        f"<div>{render_badge_group([(snapshot.get('bias_label'), 'neutral'), (snapshot.get('confidence_label'), 'ghost')])}</div>"
        f"<div class='info-grid' style='margin-top:12px'>{render_kv_chips([('最新收盘', snapshot.get('latest_close')), ('日涨跌', fmt_pct(snapshot.get('latest_pct_chg'))), ('下一交易日', fmt_forecast_window(snapshot.get('next_day'))), ('5日区间', fmt_forecast_window(snapshot.get('five_day'))), ('20日波动', fmt_pct(snapshot.get('realized_volatility_20d'))), ('趋势强度', snapshot.get('trend_strength'))])}</div>"
        f"<div class='muted' style='margin-top:12px'>主要驱动：{escape(forecast_driver_summary(snapshot, 132))}</div>"
        f"<div class='muted' style='margin-top:8px'>行情交易日：{escape(snapshot.get('latest_trade_date') or '-')} · 事件日期：{escape(event_recency)}</div>"
        f"<div class='muted' style='margin-top:8px'>最新事件：{escape(event_summary)}</div>"
        f"<div class='source-link' style='margin-top:8px'>{event_link}</div>"
        "</article>"
    )


def render_opportunity_name(item: dict, state: dict) -> str:
    ts_code = item.get("ts_code")
    name = item.get("name") or ts_code or "-"
    if find_watch_item(state, ts_code):
        return (
            f"<a href='{research_detail_href(ts_code)}'><strong>{escape(name)}</strong></a>"
            f"<div class='muted'>{escape(ts_code or '-')} · {escape(code_label(item.get('sector')))} · {escape(item.get('market') or '-')}</div>"
        )
    return (
        f"<strong>{escape(name)}</strong>"
        f"<div class='muted'>{escape(ts_code or '-')} · {escape(code_label(item.get('sector')))} · {escape(item.get('market') or '-')}</div>"
    )


def render_theme_radar_cards(items: list[dict]) -> str:
    if not items:
        return "<div class='empty'>当前还没有形成主题雷达结果。</div>"
    cards = []
    for item in items:
        leaders = "".join(
            f"<li>{escape(row.get('name') or '-')}"
            f"<span class='muted'> / {escape(row.get('ts_code') or '-')} / score {escape(fmt_number(row.get('score')))}</span></li>"
            for row in (item.get("leaders") or [])[:3]
        )
        market_text = " / ".join(f"{key} {value}" for key, value in (item.get("markets") or {}).items()) or "暂无市场分布"
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3>{escape(item.get('label') or '-')}</h3><div class='muted'>{escape(item.get('description') or '-')}</div></div>"
            f"<div>{badge(item.get('signal_label') or item.get('signal'), status_tone(item.get('signal')))}</div>"
            "</div>"
            f"<p>{escape(item.get('summary') or '-')}</p>"
            f"<div class='muted'>覆盖 {escape(fmt_number(item.get('target_count') or 0))} 个目标 / 候选 {escape(fmt_number(item.get('candidate_count') or 0))} 个 / 市场分布 {escape(market_text)}</div>"
            f"<div style='margin-top:14px'><h4>代表标的</h4><ul>{leaders or '<li>-</li>'}</ul></div>"
            "</article>"
        )
    return f"<div class='story-grid'>{''.join(cards)}</div>"


def render_opportunity_cards(title: str, items: list[dict], state: dict, empty_text: str) -> str:
    if not items:
        return (
            "<section class='panel'>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='empty'>{escape(empty_text)}</div>"
            "</section>"
        )

    cards = []
    for item in items:
        why_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("why") or [])[:4])
        risk_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("risks") or [])[:3])
        source_html = render_source_list((item.get("source_rel_paths") or [])[:4], "当前没有原文入口。")
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div>{render_opportunity_name(item, state)}</div>"
            f"<div>{badge(item.get('bucket_label') or item.get('bucket'), status_tone(item.get('bucket')))}</div>"
            "</div>"
            f"<div class='badge-row' style='margin-bottom:10px'>{badge(' / '.join(item.get('theme_labels') or ['-']), 'neutral')}{badge(item.get('primary_pool'), 'ghost')}</div>"
            f"<p>{escape(business_text(item.get('summary') or '-'))}</p>"
            f"<div class='info-grid' style='margin-top:12px'>{render_kv_chips([('机会分', item.get('undervaluation_score')), ('当前价格', item.get('latest_close')), ('日涨跌', fmt_pct(item.get('latest_pct_chg'))), ('研报空间', fmt_pct(item.get('target_gap_pct'))), ('卖方空间', fmt_pct(item.get('analyst_gap_pct'))), ('近三周事件', item.get('event_count_21d') or 0)])}</div>"
            f"<div style='margin-top:14px'><h4>为什么值得继续看</h4><ul>{why_rows or '<li>当前没有提取到明确理由。</li>'}</ul></div>"
            f"<div style='margin-top:14px'><h4>主要风险</h4><ul>{risk_rows or '<li>当前没有提取到明确风险。</li>'}</ul></div>"
            f"<div style='margin-top:14px'><h4>原文入口</h4>{source_html}</div>"
            "</article>"
        )
    return (
        "<section class='panel'>"
        f"<h2>{escape(title)}</h2>"
        "<div class='section-intro'>这里只保留已经过主题聚合和机会分排序后的业务结果，不展示原始抓取过程。</div>"
        f"{''.join(cards)}"
        "</section>"
    )


def flatten_radar_market_items(radar: dict, limit: int = 12) -> list[dict]:
    rows = []
    for market_items in (radar.get("markets") or {}).values():
        rows.extend(market_items or [])
    if not rows:
        rows = radar.get("top_candidates") or []
    rows.sort(key=lambda item: (-(item.get("opportunity_score") or 0), item.get("ts_code") or ""))
    return rows[:limit]


def render_active_radar_cards(items: list[dict], state: dict, empty_text: str) -> str:
    if not items:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    cards = []
    for item in items:
        metrics = item.get("metrics") or {}
        volume_ratio = metrics.get("volume_ratio_20d")
        volume_ratio_text = f"{volume_ratio:.2f}x" if volume_ratio not in (None, "") else "-"
        why_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("why") or [])[:3])
        risk_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("risks") or [])[:2])
        cards.append(
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div>{render_opportunity_name(item, state)}</div>"
            f"<div>{badge(item.get('radar_bucket'), status_tone(item.get('radar_bucket')))}</div>"
            "</div>"
            f"<div class='badge-row' style='margin-bottom:10px'>{badge(fmt_number(item.get('opportunity_score')), 'neutral')}{badge(' / '.join(item.get('signal_tags') or ['-']), 'ghost')}</div>"
            f"<div class='info-grid' style='margin-top:12px'>{render_kv_chips([('最新涨跌', fmt_pct(metrics.get('latest_pct_chg'))), ('5日收益', fmt_pct(metrics.get('return_5d'))), ('20日收益', fmt_pct(metrics.get('return_20d'))), ('量能倍数', volume_ratio_text), ('趋势强度', (item.get('factors') or {}).get('trend_strength')), ('主池', item.get('primary_pool') or '-')], chip_class='info-chip compact')}</div>"
            f"<div style='margin-top:14px'><h4>为什么进入雷达</h4><ul>{why_rows or '<li>当前没有足够解释。</li>'}</ul></div>"
            f"<div style='margin-top:14px'><h4>先看风险</h4><ul>{risk_rows or '<li>当前没有明确风险。</li>'}</ul></div>"
            "</article>"
        )
    return "".join(cards)


def render_strategy_evidence_table(items: list[dict]) -> str:
    rows = []
    for item in items[:12]:
        best = item.get("best_evidence") or {}
        rows.append(
            [
                render_watch_name_link({"ts_code": item.get("ts_code"), "name": item.get("name")}),
                escape(fmt_number(item.get("opportunity_score"))),
                escape(best.get("strategy_id") or "-"),
                escape(fmt_number(best.get("trade_count") or 0)),
                escape(fmt_ratio(best.get("win_rate"))),
                escape(fmt_ratio(best.get("avg_return"))),
                badge(best.get("evidence_label"), status_tone(best.get("evidence_label"))),
            ]
        )
    return render_html_table(["标的", "雷达分", "最佳策略", "交易数", "胜率", "平均收益", "证据"], rows, "当前还没有策略证据。")


def render_attack_defense_table(cases: list[dict]) -> str:
    rows = []
    for item in cases[:10]:
        attack = compact_text("；".join(item.get("attack_points") or []), 98)
        kill = compact_text("；".join(item.get("kill_triggers") or []), 98)
        rows.append(
            [
                render_watch_name_link({"ts_code": item.get("ts_code"), "name": item.get("name")}),
                badge(item.get("verdict"), status_tone(item.get("verdict"))),
                escape(compact_text(item.get("verdict_summary") or "-", 90)),
                escape(attack or "-"),
                escape(kill or "-"),
            ]
        )
    return render_html_table(["标的", "结论", "摘要", "攻击点", "失效条件"], rows, "当前还没有攻防推演。")


def render_paper_ticket_table(tickets: list[dict]) -> str:
    rows = []
    for ticket in tickets[:10]:
        levels = ticket.get("reference_levels") or {}
        rows.append(
            [
                render_watch_name_link({"ts_code": ticket.get("ts_code"), "name": ticket.get("name")}),
                badge(ticket.get("verdict"), status_tone(ticket.get("verdict"))),
                escape(fmt_number(ticket.get("opportunity_score"))),
                escape(fmt_number(levels.get("observe_above"))),
                escape(fmt_number(levels.get("invalidate_below"))),
                escape(compact_text(ticket.get("paper_trigger") or "-", 86)),
            ]
        )
    return render_html_table(["标的", "纸面状态", "分数", "观察上沿", "失效下沿", "触发说明"], rows, "当前还没有纸面观察单。")


def render_lifecycle_table(items: list[dict]) -> str:
    rows = []
    for item in items[:12]:
        rows.append(
            [
                render_watch_name_link({"ts_code": item.get("ts_code"), "name": item.get("name")}),
                badge(item.get("lifecycle_state"), status_tone(item.get("lifecycle_state"))),
                escape(fmt_number(item.get("current_score"))),
                escape(fmt_number(item.get("score_delta"))),
                escape(fmt_number(item.get("seen_snapshot_count") or 0)),
                badge(item.get("evidence_label") or item.get("attack_verdict") or "-", status_tone(item.get("evidence_label") or item.get("attack_verdict"))),
                escape(compact_text(item.get("next_action") or "-", 88)),
            ]
        )
    return render_html_table(["标的", "生命周期", "当前分", "变化", "出现", "证据", "下一步"], rows, "当前还没有机会生命周期快照。")


def render_paper_performance_table(items: list[dict]) -> str:
    rows = []
    for item in items[:12]:
        rows.append(
            [
                render_watch_name_link({"ts_code": item.get("ts_code"), "name": item.get("name")}),
                badge(item.get("status"), status_tone(item.get("status"))),
                escape(fmt_number(item.get("days_tracked") or 0)),
                escape(fmt_pct(item.get("latest_return"))),
                escape(f"{fmt_pct(item.get('best_return'))} / {fmt_pct(item.get('worst_return'))}"),
                escape(item.get("observe_hit_date") or "-"),
                escape(item.get("invalidate_hit_date") or "-"),
                escape(compact_text(item.get("action") or "-", 82)),
            ]
        )
    return render_html_table(["标的", "状态", "跟踪日", "最新收益", "最好/最差", "触发日", "失效日", "下一步"], rows, "当前还没有纸面表现复盘。")


def render_event_table(items: list[dict]) -> str:
    rows = []
    for item in items:
        source_rel_path = item.get("source_rel_path")
        source_html = f"<a href='/artifact?path={quote(source_rel_path)}'>{escape(source_rel_path)}</a>" if source_rel_path else "-"
        rows.append(
            "<tr>"
            f"<td>{escape(item.get('publish_time') or item.get('event_date') or '-')}</td>"
            f"<td>{escape(item.get('entity_id') or '-')}</td>"
            f"<td>{escape(item.get('title') or '-')}</td>"
            f"<td>{badge(item.get('importance'), 'ghost')}</td>"
            f"<td>{source_html}</td>"
            "</tr>"
        )
    return "".join(rows) or "<tr><td colspan='5' class='empty'>暂无事件</td></tr>"


def portal_tile(title: str, href: str, description: str, bullets: list[str]) -> str:
    bullet_html = "".join(f"<li>{escape(business_text(item, 90))}</li>" for item in bullets if item)
    if not bullet_html:
        bullet_html = "<li>当前暂无可展示结果。</li>"
    return (
        f"<a class='tile' href='{href}'>"
        f"<h2 class='tile-title'>{escape(title)}</h2>"
        f"<p>{escape(description)}</p>"
        f"<ul>{bullet_html}</ul>"
        "</a>"
    )


def iso_date_gap_days(expected_date: str | None, actual_date: str | None) -> int | None:
    if expected_date in (None, "") or actual_date in (None, ""):
        return None
    try:
        expected = dt_date.fromisoformat(str(expected_date))
        actual = dt_date.fromisoformat(str(actual_date))
    except ValueError:
        return None
    return max((expected - actual).days, 0)


def render_operation_run_cell(run: dict | None) -> str:
    snapshot = run or {}
    if not snapshot:
        return "<span class='muted'>今天还没有跑到这条链。</span>"
    status = snapshot.get("status")
    finished_at = snapshot.get("finished_at") or snapshot.get("started_at") or "-"
    command_count = snapshot.get("command_count")
    summary_link = (
        f"<div class='story-footer' style='margin-top:8px'>{link_for_rel_path(snapshot.get('summary_rel_path'), '查看运行摘要')}</div>"
        if snapshot.get("summary_rel_path")
        else ""
    )
    return (
        f"{badge(status, status_tone(status))}"
        f"<div class='muted' style='margin-top:8px'>{escape(finished_at)} · {escape(fmt_number(command_count or 0))} 步</div>"
        f"{summary_link}"
    )


def render_home_focus_list(actions: list, empty_text: str = "当前没有需要置顶处理的事项。") -> str:
    if not actions:
        return f"<div class='empty'>{escape(empty_text)}</div>"
    rows = []
    for index, action in enumerate(actions[:4], start=1):
        if isinstance(action, dict):
            title = home_status_text(action.get("title"), 92)
            note = home_status_text(action.get("note"), 112) if action.get("note") else ""
            href = action.get("href")
            cta = action.get("cta") or "查看"
        else:
            title = home_status_text(action, 92)
            note = ""
            href = None
            cta = "查看"
        note_html = f"<div class='focus-note'>{escape(note)}</div>" if note else ""
        action_html = (
            f"<div class='focus-actions'><a class='small-button' href='{escape(str(href))}'>{escape(str(cta))}</a></div>"
            if href
            else ""
        )
        rows.append(
            "<li>"
            f"<span class='focus-index'>{index}</span>"
            "<div class='focus-main'>"
            f"<div class='focus-title'>{escape(title)}</div>"
            f"{note_html}"
            "</div>"
            f"{action_html}"
            "</li>"
        )
    return f"<ol class='focus-list'>{''.join(rows)}</ol>"


def home_status_text(value: str | None, limit: int | None = None) -> str:
    text = business_text(value)
    text = text.replace("patch 候选池", "patch 候选稿")
    if limit is not None and len(text) > limit:
        return f"{text[: limit - 1].rstrip()}…"
    return text


def render_home_opportunity_rows(
    items: list[dict],
    actions: list[dict],
    paper_watch: list[dict],
    limit: int = 3,
) -> str:
    if not items:
        return "<div class='empty'>当前没有高优先机会。</div>"
    cards = [
        "<div class='section-intro'>"
        "置顶按机会分排序：短线涨跌、5/20日收益、量能、趋势强度、20日突破、池子级别、研究/事件锚点共同加分；RSI 过热和单日追高会扣分。"
        "它不是自动买入清单，只有穿过组合动作门禁的标的才给出试单金额。"
        "</div>"
    ]
    for rank, item in enumerate(items[:limit], start=1):
        name = item.get("name") or item.get("ts_code") or "-"
        ts_code = item.get("ts_code") or ""
        metrics = item.get("metrics") or {}
        factors = item.get("factors") or {}
        action = find_action_for_buy_or_subject(actions, ts_code)
        paper_ticket = find_paper_watch_ticket(paper_watch, ts_code)
        add_leg = (action or {}).get("add") or {}
        is_buy_action = action and add_leg.get("ts_code") == ts_code and (action.get("gate_status") == "ready")
        if is_buy_action:
            decision = "可做换仓试单"
            trade_text = (
                f"规模：约 {fmt_money_cn(action.get('trade_amount'))} / {fmt_ratio(action.get('trade_amount_pct'))}"
                f"；估算股数：{extract_trial_shares(action)}"
            )
            action_href = action_detail_href(action.get("action_id"))
            action_cta = "看买入方案"
        elif action:
            decision = "先复核，不新增买入"
            trade_text = "规模：当前不新增仓位；先看已有持仓/候选是否还能留在主线。"
            action_href = action_detail_href(action.get("action_id"))
            action_cta = "看复核详情"
        else:
            decision = "只观察，不下单"
            trade_text = "规模：0；等连续信号和研究链补齐后再升级到动作建议。"
            action_href = research_detail_href(ts_code)
            action_cta = "看标的详情"
        observe_text = (
            f"观察上沿 {fmt_number(paper_ticket.get('observe_above'))}；失效下沿 {fmt_number(paper_ticket.get('invalidate_below'))}"
            if paper_ticket
            else "暂无纸面观察价位；先补研究和下一交易日量价验证。"
        )
        volume_ratio = metrics.get("volume_ratio_20d")
        volume_ratio_text = f"{volume_ratio:.2f}x" if volume_ratio is not None else "-"
        why = "；".join((item.get("why") or [])[:2])
        risk = compact_text((item.get("risks") or [""])[0], 96)
        buy_after = compact_text((item.get("next_checks") or [""])[0], 96)
        target_text = "目标价：当前没有统一目标价口径；先用观察上沿/失效下沿做触发与风控，目标价需在详情链补齐。"
        cards.append(
            "<article class='action-card'>"
            "<div class='action-topline'>"
            "<div>"
            f"<h3 class='action-title'>#{rank} {escape(name)} / {escape(ts_code or '-')}</h3>"
            f"<div class='focus-note'>机会分 {escape(fmt_number(item.get('opportunity_score')))}；池子 {escape(code_label(item.get('primary_pool')))}；{escape(' / '.join(code_label(tag) for tag in (item.get('signal_tags') or [])[:3]))}</div>"
            "</div>"
            f"{badge(decision, 'good' if is_buy_action else 'warning' if action else 'neutral')}"
            "</div>"
            f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips([('最新价', metrics.get('latest_close')), ('日涨跌', fmt_pct(metrics.get('latest_pct_chg'))), ('5日', fmt_pct(metrics.get('return_5d'))), ('20日', fmt_pct(metrics.get('return_20d'))), ('量能', volume_ratio_text), ('热度RSI', factors.get('rsi_14'))], chip_class='info-chip compact')}</div>"
            f"<p class='action-copy'>为什么置顶：{escape(why or '由机会分排序进入前三。')}</p>"
            f"<p class='action-copy'>怎么操作：{escape(decision)}；{escape(trade_text)}</p>"
            f"<p class='action-copy'>买价/风控：最新价 {escape(fmt_number(metrics.get('latest_close')))}；{escape(observe_text)}</p>"
            f"<p class='action-copy'>买后观察：{escape(buy_after or '-')}</p>"
            f"<p class='action-copy'>{escape(target_text)}</p>"
            f"<p class='action-copy'>主要风险：{escape(risk or '暂无突出风险备注。')}</p>"
            "<div class='button-row'>"
            f"<a class='small-button' href='{action_href}'>{escape(action_cta)}</a>"
            f"<a class='small-button' href='{research_detail_href(ts_code)}'>看研究详情</a>"
            "</div>"
            "</article>"
        )
    return "".join(cards)


def render_home_gap_rows(items: list[dict], limit: int = 3) -> str:
    if not items:
        return "<div class='empty'>当前没有置顶证据缺口。</div>"
    rows = []
    for item in items[:limit]:
        name = item.get("name") or item.get("ts_code") or "-"
        ts_code = item.get("ts_code") or ""
        latest = item.get("latest_source_updated_at") or ((item.get("latest_event") or {}).get("publish_time")) or "-"
        action = compact_text(item.get("recommended_action"), 68)
        subject = f"<a href='{research_detail_href(ts_code)}'>{escape(name)}</a>" if ts_code else escape(name)
        rows.append(
            "<div class='watch-row'>"
            "<div>"
            f"<div class='focus-title'>{subject}</div>"
            f"<div class='focus-note'>{escape(ts_code or '-')} · {escape(latest)}</div>"
            f"<div class='focus-note'>{escape(action or '补公开来源后再升级判断。')}</div>"
            "</div>"
            f"{badge(item.get('evidence_state'), status_tone(item.get('evidence_state')))}"
            "</div>"
        )
    return "".join(rows)


def find_action_for_sell(actions: list[dict], ts_code: str | None) -> dict | None:
    if not ts_code:
        return None
    for action in actions:
        remove_code = ((action.get("remove") or {}).get("ts_code"))
        subject_code = ((action.get("subject") or {}).get("ts_code"))
        if ts_code in {remove_code, subject_code}:
            return action
    return None


def find_action_for_buy_or_subject(actions: list[dict], ts_code: str | None) -> dict | None:
    if not ts_code:
        return None
    for action in actions:
        add_code = ((action.get("add") or {}).get("ts_code"))
        subject_code = ((action.get("subject") or {}).get("ts_code"))
        if ts_code in {add_code, subject_code}:
            return action
    return None


def find_paper_watch_ticket(items: list[dict], ts_code: str | None) -> dict | None:
    if not ts_code:
        return None
    for item in items:
        if item.get("ts_code") == ts_code:
            return item
    return None


def extract_trial_shares(action: dict | None) -> str:
    if not action:
        return "-"
    checks = " ".join(str(item) for item in (action.get("next_checks") or []))
    match = re.search(r"可先试\s*`?([0-9,]+)`?\s*股", checks)
    return f"{match.group(1)} 股" if match else "-"


def render_home_risk_cards(sell_candidates: list[dict], actions: list[dict]) -> str:
    actionable = [
        item for item in sell_candidates
        if str(item.get("verdict") or "").lower() in {"sell", "trim"}
    ]
    if not actionable:
        return "<div class='empty'>当前没有需要立刻处理的卖出侧对象。</div>"
    cards = []
    for item in actionable[:3]:
        linked_buy = item.get("linked_buy") or {}
        linked_text = f"；可对换：{linked_buy.get('name')} / {linked_buy.get('ts_code')}" if linked_buy else ""
        action = find_action_for_sell(actions, item.get("ts_code"))
        href = action_detail_href(action.get("action_id")) if action else research_detail_href(item.get("ts_code"))
        why = compact_text("；".join(item.get("why") or []), 96)
        next_check = compact_text((item.get("next_checks") or [""])[0], 88)
        cards.append(
            "<article class='action-card'>"
            "<div class='action-topline'>"
            "<div>"
            f"<h3 class='action-title'>{escape(item.get('name') or '-')} / {escape(item.get('ts_code') or '-')}</h3>"
            f"<div class='focus-note'>{escape(item.get('summary') or '-')}{escape(linked_text)}</div>"
            "</div>"
            f"{badge(item.get('verdict_label') or item.get('verdict'), status_tone(item.get('verdict')))}"
            "</div>"
            f"<p class='action-copy'>原因：{escape(why or '-')}</p>"
            f"<p class='action-copy'>下一步：{escape(next_check or '-')}</p>"
            f"<div class='button-row'><a class='small-button' href='{href}'>看处理方案</a></div>"
            "</article>"
        )
    return "".join(cards)


def render_home_action_cards(actions: list[dict], limit: int = 5) -> str:
    if not actions:
        return "<div class='empty'>当前没有动作建议。</div>"
    cards = []
    for action in actions[:limit]:
        href = action_detail_href(action.get("action_id"))
        next_check = compact_text((action.get("next_checks") or [""])[0], 92)
        risk = compact_text((action.get("risk_flags") or [""])[0], 86)
        cards.append(
            "<article class='action-card'>"
            "<div class='action-topline'>"
            "<div>"
            f"<h3 class='action-title'>{escape(action.get('title') or '-')}</h3>"
            f"<div class='focus-note'>{escape(action.get('summary') or '-')}</div>"
            "</div>"
            f"{badge(action.get('priority'), status_tone(action.get('priority')))}"
            "</div>"
            f"<p class='action-copy'>下一步：{escape(next_check or '-')}</p>"
            f"<p class='action-copy'>注意：{escape(risk or '-')}</p>"
            f"<div class='button-row'><a class='small-button' href='{href}'>看建议详情</a></div>"
            "</article>"
        )
    return "".join(cards)


def render_home_paper_watch_cards(items: list[dict], artifact: dict | None = None, limit: int = 4) -> str:
    if not items:
        return "<div class='empty'>当前没有纸面观察对象。</div>"
    cards = []
    for item in items[:limit]:
        subject = f"{item.get('name') or '-'} / {item.get('ts_code') or '-'}"
        observe = fmt_number(item.get("observe_above"))
        invalidate = fmt_number(item.get("invalidate_below"))
        href = research_detail_href(item.get("ts_code"))
        cards.append(
            "<article class='action-card'>"
            "<div class='action-topline'>"
            "<div>"
            f"<h3 class='action-title'>{escape(subject)}</h3>"
            f"<div class='focus-note'>观察上沿 {escape(observe)}；失效下沿 {escape(invalidate)}</div>"
            "</div>"
            f"{badge(item.get('performance_status') or item.get('verdict'), status_tone(item.get('performance_status') or item.get('verdict')))}"
            "</div>"
            f"<p class='action-copy'>{escape(item.get('action') or '等待新行情后再评价。')}</p>"
            f"<div class='button-row'><a class='small-button' href='{href}'>看标的详情</a></div>"
            "</article>"
        )
    artifact_link = (
        f"<div class='source-link'>{link_for_rel_path((artifact or {}).get('rel_path'), '查看完整纸面观察单')}</div>"
        if artifact
        else ""
    )
    return "".join(cards) + artifact_link


def build_home_focus_items(sell_candidates: list[dict], actions: list[dict], paper_watch: list[dict]) -> list[dict]:
    focus_items: list[dict] = []
    actionable = [
        item for item in sell_candidates
        if str(item.get("verdict") or "").lower() in {"sell", "trim"}
    ]
    for index, item in enumerate(actionable[:2]):
        action = find_action_for_sell(actions, item.get("ts_code"))
        href = action_detail_href(action.get("action_id")) if action else research_detail_href(item.get("ts_code"))
        label = item.get("verdict_label") or code_label(item.get("verdict"))
        subject = f"{item.get('name') or '-'} / {item.get('ts_code') or '-'}"
        prefix = "先处理" if index == 0 else "再处理"
        summary = compact_text(item.get("summary") or "", 48)
        action_title = action.get("title") if action else ""
        plan = f"方案：{action_title}" if action_title else "进入标的详情看风险依据。"
        note = "；".join(part for part in [summary, plan] if part)
        focus_items.append(
            {
                "title": f"{prefix} {subject}：{label}",
                "note": note,
                "href": href,
                "cta": "看处理方案",
            }
        )
    if actions:
        high_count = sum(1 for action in actions if str(action.get("priority") or "").lower() in {"high", "高"})
        watch_count = max(len(actions) - high_count, 0)
        focus_items.append(
            {
                "title": f"{len(actions)}条动作建议：先看{high_count or 0}条高优先级换仓",
                "note": f"其余{watch_count}条先做观察或复核，不混进交易决策。",
                "href": "#actions",
                "cta": "看全部建议",
            }
        )
    if paper_watch:
        names = "、".join(str(item.get("name") or item.get("ts_code") or "-") for item in paper_watch[:3])
        focus_items.append(
            {
                "title": f"纸面观察{len(paper_watch)}个：只盯突破/失效",
                "note": f"先看{names or '当前标的'}的观察上沿和失效下沿；这不是交易指令。",
                "href": "#paper-watch",
                "cta": "看观察位",
            }
        )
    return focus_items[:4]


def render_home_entry_links(entries: list[tuple[str, str, str]]) -> str:
    return "<div class='entry-grid'>" + "".join(
        f"<a class='entry-link' href='{escape(href)}'>"
        f"<strong>{escape(title)}</strong>"
        f"<span>{escape(note)}</span>"
        "</a>"
        for title, href, note in entries
    ) + "</div>"


def render_home(state: dict, refresh_seconds: int) -> str:
    overview = state["overview"]
    current_state = state.get("current_state") or {}
    opportunity_engine = state.get("opportunity_engine") or {}
    radar = opportunity_engine.get("radar") or {}
    paper_watchlist = opportunity_engine.get("paper_watchlist") or {}
    portfolio = state.get("portfolio_action") or {}
    risk_decision = (state.get("risk") or {}).get("decision") or {}
    top_opportunities = current_state.get("top_opportunities") or (radar.get("top_candidates") or [])
    paper_watch = current_state.get("paper_watch") or []
    actions = portfolio.get("actions") or []
    sell_candidates = risk_decision.get("sell_candidates") or []
    paper_watch_artifact = (paper_watchlist or {}).get("artifact")
    focus_items = build_home_focus_items(sell_candidates, actions, paper_watch)
    hero_summary = (
        focus_items[0].get("title")
        if focus_items
        else "当前没有需要立刻处理的组合动作。"
    )
    risk_count = sum(
        1 for item in sell_candidates
        if str(item.get("verdict") or "").lower() in {"sell", "trim"}
    )
    body = (
        "<section class='command-layout'>"
        "<article class='panel'>"
        "<h2>今日只看</h2>"
        f"{render_home_focus_list(focus_items, '当前没有需要立刻处理的组合动作。')}"
        "</article>"
        "<article class='panel' id='risk'>"
        "<h2>先处理风险</h2>"
        "<div class='section-intro'>这里直接列出“卖出侧高优先级对象”是谁，以及对应处理方案。</div>"
        f"{render_home_risk_cards(sell_candidates, actions)}"
        "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel' id='actions'>"
        f"<h2>{escape(fmt_number(len(actions)))}条动作建议</h2>"
        "<div class='section-intro'>这里就是动作建议本身，每条都可以点进详情。</div>"
        f"{render_home_action_cards(actions, limit=5)}"
        "</article>"
        "<article class='panel' id='paper-watch'>"
        "<h2>纸面观察什么</h2>"
        "<div class='section-intro'>纸面观察不是交易指令，只记录哪些标的需要看突破/失效。</div>"
        f"{render_home_paper_watch_cards(paper_watch, paper_watch_artifact, limit=4)}"
        "</article>"
        "</section>"
        "<section>"
        "<article class='panel'>"
        "<h2>置顶机会怎么操作</h2>"
        f"{render_home_opportunity_rows(top_opportunities, actions, paper_watch)}"
        "</article>"
        "</section>"
    )
    return render_shell(
        page_title="SMR 前台看板",
        current_path="/",
        hero_title="SMR 前台看板",
        hero_subtitle=home_status_text(hero_summary, 108),
        hero_facts=[
            ("风险对象", risk_count),
            ("动作建议", len(actions)),
            ("纸面观察", len(paper_watch) or (paper_watchlist.get("ticket_count") or 0)),
            ("最新行情", overview.get("a_share_trade_date") or "-"),
        ],
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


DASHBOARD_BRAND = "同行资本投研系统"


def _tone_class(tone: str | None) -> str:
    tone_map = {
        "good": "tone-good",
        "success": "tone-good",
        "warning": "tone-warning",
        "warn": "tone-warning",
        "danger": "tone-danger",
        "error": "tone-danger",
        "info": "tone-info",
        "muted": "tone-muted",
    }
    return tone_map.get((tone or "").lower(), "tone-muted")


def render_today_overview(state: dict, refresh_seconds: int) -> str:
    view = build_today_overview_view_model(state)
    metrics = view["metrics"]
    top_changes = view["top_changes"]
    pending = view["pending_decisions"]
    coverage = view["coverage_moves"]
    health = view["health_summary"]
    updated_at = view["updated_at"]
    empty = view["empty_state"]

    metric_cards_html = render_today_metric_cards(metrics)
    top_changes_html = render_top_changes(top_changes, empty)
    pending_html = render_pending_decisions(pending, empty)
    coverage_html = render_coverage_moves(coverage, empty)
    health_html = render_health_summary(health, empty)

    body = f"""
<section class="today-metrics">
  {metric_cards_html}
</section>
<section class="today-grid">
  <article class="panel today-main">
    <h2 class="today-section-title">今日最重要的 3 件事</h2>
    {top_changes_html}
  </article>
  <div class="today-side">
    <article class="panel">
      <h2 class="today-section-title">今日待判断</h2>
      {pending_html}
    </article>
    <article class="panel">
      <h2 class="today-section-title">覆盖池异动</h2>
      {coverage_html}
    </article>
    <article class="panel">
      <h2 class="today-section-title">数据健康提醒</h2>
      {health_html}
    </article>
  </div>
</section>
<div class="today-footer">
  <span class="muted">最近更新：{escape(updated_at)}</span>
</div>
<div class="today-disclaimer">
  系统仅展示证据与信号，不直接给出投资建议。不提供任何投资建议。
</div>
"""
    return render_shell(
        page_title="今日总览 · 同行资本投研系统",
        current_path="/",
        hero_title="今日总览",
        hero_subtitle="今天最值得关注的变化与待判断事项",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def render_today_metric_cards(metrics: dict) -> str:
    cards = []
    configs = [
        ("important_changes", "今日重点变化", "#3b82f6", "chart-line"),
        ("pending_decisions", "待判断事项", "#f59e0b", "question-circle"),
        ("high_priority_companies", "高优先级公司", "#10b981", "building"),
        ("risk_alerts", "风险提示", "#ef4444", "shield"),
    ]
    for key, label, color, icon in configs:
        m = metrics.get(key) or {}
        count = m.get("count", 0)
        subtitle = m.get("subtitle", "")
        cards.append(
            f"""
<div class="metric-card">
  <div class="metric-icon" style="background: {color}15; color: {color};">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      {_metric_icon(icon)}
    </svg>
  </div>
  <div class="metric-body">
    <div class="metric-label">{escape(label)}</div>
    <div class="metric-value" style="color: {color};">{escape(str(count))} 条</div>
    <div class="metric-subtitle muted">{escape(subtitle)}</div>
  </div>
</div>
"""
        )
    return "\n".join(cards)


def _metric_icon(name: str) -> str:
    icons = {
        "chart-line": '<path d="M3 3v18h18"/><path d="M19 9l-5 5-4-4-3 3"/>',
        "question-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
        "building": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
        "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    }
    return icons.get(name, "")


def render_top_changes(items: list[dict], empty: bool) -> str:
    if not items or empty:
        return """
<div class="empty-state">
  <div class="empty-state-title">暂无今日重点变化</div>
  <div class="empty-state-desc">系统尚未生成足够证据，建议查看信号流或数据健康。</div>
</div>
"""
    cards = []
    for item in items:
        rank = item.get("rank", 0)
        title = item.get("title", "")
        entities = item.get("affected_entities") or []
        summary = item.get("summary", "")
        strength = item.get("evidence_strength", "")
        source_type = item.get("source_type", "")
        strength_tone = "good" if strength == "高" else "warning" if strength == "中" else "muted"
        entities_text = "、".join(entities) if entities else ""
        cards.append(
            f"""
<div class="change-card">
  <div class="change-rank">{escape(str(rank))}</div>
  <div class="change-body">
    <div class="change-title">{escape(title)}</div>
    <div class="change-entities">{escape(entities_text)}</div>
    <div class="change-summary muted">{escape(summary)}</div>
  </div>
  <div class="change-side">
    <span class="badge badge-{strength_tone}">{escape(strength)}</span>
    <span class="badge badge-info">{escape(source_type)}</span>
  </div>
</div>
"""
        )
    return "\n".join(cards)


def render_pending_decisions(items: list[dict], empty: bool) -> str:
    if not items or empty:
        return """
<div class="empty-state small">
  <div class="empty-state-title">暂无待判断事项</div>
  <div class="empty-state-desc">当前没有需要人工确认的关键事项。</div>
</div>
"""
    rows = []
    for item in items:
        rank = item.get("rank", 0)
        question = item.get("question", "")
        badge = item.get("status_badge", "")
        tone = item.get("badge_tone", "muted")
        rows.append(
            f"""
<div class="pending-row">
  <span class="pending-rank">{escape(str(rank))}</span>
  <span class="pending-question">{escape(question)}</span>
  <span class="badge badge-{tone}">{escape(badge)}</span>
</div>
"""
        )
    return "\n".join(rows)


def render_coverage_moves(items: list[dict], empty: bool) -> str:
    if not items or empty:
        return """
<div class="empty-state small">
  <div class="empty-state-title">暂无覆盖池异动</div>
  <div class="empty-state-desc">覆盖池中暂无显著变化。</div>
</div>
"""
    rows = []
    for item in items:
        company = item.get("company", "")
        status_label = item.get("status_label", "")
        status_tone = item.get("status_tone", "muted")
        evidence_pct = item.get("evidence_pct", 0)
        priority = item.get("priority", "")
        priority_tone = "danger" if priority == "高" else "warning" if priority == "中" else "muted"
        rows.append(
            f"""
<tr>
  <td class="cov-company">{escape(company)}</td>
  <td><span class="status-dot {_tone_class(status_tone)}"></span>{escape(status_label)}</td>
  <td>
    <div class="evidence-bar">
      <div class="evidence-bar-fill" style="width: {evidence_pct}%;"></div>
    </div>
    <span class="evidence-pct muted">{evidence_pct}%</span>
  </td>
  <td><span class="badge badge-{priority_tone}">{escape(priority)}</span></td>
</tr>
"""
        )
    return f"""
<div class="coverage-table-wrap">
  <table class="coverage-table">
    <thead>
      <tr>
        <th>公司</th>
        <th>最新状态</th>
        <th>证据完整度</th>
        <th>优先级</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>
"""


def render_health_summary(items: list[dict], empty: bool) -> str:
    if not items:
        items = [
            {"label": "行情新鲜度", "status": "暂无数据", "tone": "muted"},
            {"label": "信息源状态", "status": "暂无数据", "tone": "muted"},
            {"label": "Pipeline 状态", "status": "暂无数据", "tone": "muted"},
        ]
    cards = []
    for item in items:
        label = item.get("label", "")
        status = item.get("status", "")
        tone = item.get("tone", "muted")
        tone_cls = _tone_class(tone)
        icon = "✓" if tone in ("good", "success") else "!" if tone in ("danger", "error") else "○"
        cards.append(
            f"""
<div class="health-card">
  <div class="health-icon {tone_cls}">{icon}</div>
  <div class="health-body">
    <div class="health-label">{escape(label)}</div>
    <div class="health-status {tone_cls}">{escape(status)}</div>
  </div>
</div>
"""
        )
    return f'<div class="health-grid">{"".join(cards)}</div>'


def render_placeholder_page(title: str, desc: str, current_path: str, state: dict, refresh_seconds: int) -> str:
    body = f"""
<div class="placeholder-page">
  <div class="placeholder-icon">📋</div>
  <h2 class="placeholder-title">{escape(title)}</h2>
  <p class="placeholder-desc">{escape(desc)}</p>
  <div class="placeholder-note muted">页面设计已完成，施工将在后续阶段进行。</div>
</div>
"""
    return render_shell(
        page_title=f"{title} · 同行资本投研系统",
        current_path=current_path,
        hero_title=title,
        hero_subtitle=desc,
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def _render_coverage_metrics(metrics: dict) -> str:
    cards = []
    for key, label in [
        ("company_count", "覆盖公司数"),
        ("industry_count", "覆盖行业/主题数"),
        ("high_priority_count", "高优先级对象"),
        ("evidence_completeness", "证据完整度"),
    ]:
        m = metrics.get(key) or {}
        if key == "evidence_completeness":
            value = f"{m.get('value', 0)}%"
        else:
            value = str(m.get("count", 0))
        subtitle = m.get("subtitle") or label
        cards.append(
            f'<article class="coverage-metric-card">'
            f'<div class="coverage-metric-value">{escape(value)}</div>'
            f'<div class="coverage-metric-subtitle">{escape(subtitle)}</div>'
            f'</article>'
        )
    return f'<section class="coverage-metrics">{"".join(cards)}</section>'


def _render_coverage_filters(filters: dict) -> str:
    type_options = [("all", "全部类型"), ("company", "公司"), ("industry", "行业"), ("theme", "主题")]
    priority_options = [("all", "全部优先级"), ("高", "高"), ("中", "中"), ("低", "低")]
    status_options = [
        ("all", "全部状态"),
        ("跟踪中", "跟踪中"),
        ("重点研究", "重点研究"),
        ("需补证据", "需补证据"),
        ("边际改善", "边际改善"),
        ("风险上升", "风险上升"),
        ("暂缓", "暂缓"),
    ]

    def _opts(opts, current):
        return "".join(
            f'<option value="{escape(v)}"{" selected" if v == current else ""}>{escape(l)}</option>'
            for v, l in opts
        )

    return f'''
<form class="coverage-filter-bar" method="get" action="/coverage">
  <div class="coverage-filter-group">
    <select class="coverage-filter-select" name="type" onchange="this.form.submit()">
      {_opts(type_options, filters.get("type", "all"))}
    </select>
  </div>
  <div class="coverage-filter-group">
    <select class="coverage-filter-select" name="priority" onchange="this.form.submit()">
      {_opts(priority_options, filters.get("priority", "all"))}
    </select>
  </div>
  <div class="coverage-filter-group">
    <select class="coverage-filter-select" name="status" onchange="this.form.submit()">
      {_opts(status_options, filters.get("status", "all"))}
    </select>
  </div>
  <input type="text" class="coverage-search" name="q" placeholder="搜索..." value="{escape(filters.get("q", ""))}">
  <button type="submit" class="coverage-filter-select" style="cursor:pointer">搜索</button>
</form>
'''


def _render_coverage_table(items: list[dict], empty: bool, filters: dict, pagination: dict) -> str:
    if empty:
        return f'''
<div class="coverage-table-section">
  <div class="coverage-table-header">
    <span class="coverage-table-title">覆盖对象列表</span>
  </div>
  {_render_coverage_filters(filters)}
  <div class="coverage-empty-state">
    <div class="coverage-empty-state-title">暂无覆盖对象</div>
    <div>当前没有可展示的覆盖公司、行业或主题。请检查数据健康或等待系统生成覆盖快照。</div>
  </div>
</div>
'''

    rows = []
    for idx, item in enumerate(items):
        name = escape(item.get("name") or "")
        typ = escape(item.get("type") or "")
        status = escape(item.get("status") or "")
        priority = escape(item.get("priority") or "")
        ev_pct = item.get("evidence_completeness", 0)
        updated = escape(item.get("updated_at") or "")
        progress_class = "high" if ev_pct >= 70 else ("medium" if ev_pct >= 40 else "low")
        rows.append(
            f'<tr class="{"selected" if idx == 0 else ""}">'
            f'<td><strong>{name}</strong></td>'
            f'<td><span class="coverage-badge type-{typ}">{typ}</span></td>'
            f'<td><span class="coverage-badge status-{status[:2]}">{status}</span></td>'
            f'<td>'
            f'<div class="coverage-progress"><div class="coverage-progress-bar {progress_class}" style="width:{ev_pct}%"></div></div>'
            f'</td>'
            f'<td><span class="coverage-badge priority-{priority}">{priority}</span></td>'
            f'<td style="color:var(--muted);font-size:12px">{updated}</td>'
            f'</tr>'
        )

    page = pagination.get("page", 1)
    total_pages = pagination.get("total_pages", 1)
    total_items = pagination.get("total_items", 0)

    page_buttons = []
    for p in range(1, total_pages + 1):
        if p == 1 or p == total_pages or abs(p - page) <= 1:
            active = " active" if p == page else ""
            page_buttons.append(
                f'<a href="/coverage?type={escape(filters.get("type","all"))}&priority={escape(filters.get("priority","all"))}&status={escape(filters.get("status","all"))}&q={escape(filters.get("q",""))}&page={p}" class="coverage-page-btn{active}">{p}</a>'
            )
        elif abs(p - page) == 2:
            page_buttons.append('<span style="color:var(--muted)">...</span>')

    pagination_html = ""
    if total_pages > 1:
        pagination_html = f'''
<div class="coverage-pagination">
  <span class="coverage-pagination-info">共 {total_items} 条</span>
  {"".join(page_buttons)}
</div>
'''

    return f'''
<div class="coverage-table-section">
  <div class="coverage-table-header">
    <span class="coverage-table-title">覆盖对象列表</span>
  </div>
  {_render_coverage_filters(filters)}
  <table class="coverage-table">
    <thead>
      <tr>
        <th>名称</th>
        <th>类型</th>
        <th>最新状态</th>
        <th>证据完整度</th>
        <th>优先级</th>
        <th>最近更新</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
  {pagination_html}
</div>
'''


def _render_coverage_detail(detail: dict) -> str:
    if detail.get("data_status") == "empty_state":
        return '''
<div class="coverage-detail-panel">
  <div class="coverage-empty-state">
    <div class="coverage-empty-state-title">请选择覆盖对象</div>
    <div>当前没有可展示的覆盖详情。</div>
  </div>
</div>
'''

    name = escape(detail.get("name") or "")
    typ = escape(detail.get("type") or "")
    priority = escape(detail.get("priority") or "")
    badges_html = ""
    for badge in (detail.get("badges") or []):
        if badge:
            badges_html += f'<span class="coverage-badge type-{badge}">{escape(badge)}</span>'
    if priority:
        badges_html += f'<span class="coverage-badge priority-{priority}">{priority}优先级</span>'

    focus_points = detail.get("focus_points") or []
    focus_html = ""
    if focus_points:
        chips = "".join(f'<span class="coverage-focus-chip">{escape(fp)}</span>' for fp in focus_points if fp)
        focus_html = f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">投资关注点</div>
  <div class="coverage-focus-list">{chips}</div>
</div>
'''

    signals = detail.get("latest_signals") or []
    signals_html = ""
    if signals:
        sig_items = []
        for sig in signals:
            direction = sig.get("signal_direction") or "待确认"
            dir_class = {
                "新增证据": "new",
                "边际改善": "improve",
                "需关注": "watch",
                "风险提示": "risk",
                "待确认": "pending",
            }.get(direction, "pending")
            sig_items.append(
                f'<div class="coverage-signal-item">'
                f'<div>'
                f'<div class="coverage-signal-title">{escape(sig.get("signal_title") or "")}</div>'
                f'<div class="coverage-signal-meta">{escape(sig.get("source_type") or "")} · {escape(sig.get("signal_date") or "")}</div>'
                f'</div>'
                f'<span class="coverage-signal-direction {dir_class}">{escape(direction)}</span>'
                f'</div>'
            )
        signals_html = f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">最新关键信号</div>
  <div class="coverage-signal-list">{"".join(sig_items)}</div>
</div>
'''

    ev = detail.get("evidence_overview") or {}
    completeness = ev.get("completeness", 0)
    covered = ev.get("covered_count", 0)
    partial = ev.get("partial_count", 0)
    missing = ev.get("missing_count", 0)
    p_covered = int(completeness / 100 * 360)
    p_partial = int((completeness + (100 - completeness) * 0.4) / 100 * 360)

    evidence_html = f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">证据概览</div>
  <div class="coverage-evidence-overview">
    <div class="coverage-donut" style="--p-covered:{p_covered}deg;--p-partial:{p_partial}deg;">
      <div class="coverage-donut-label">{completeness}%</div>
    </div>
    <div class="coverage-evidence-legend">
      <div class="coverage-evidence-legend-item"><span class="coverage-evidence-dot covered"></span> 已覆盖 {covered}</div>
      <div class="coverage-evidence-legend-item"><span class="coverage-evidence-dot partial"></span> 部分覆盖 {partial}</div>
      <div class="coverage-evidence-legend-item"><span class="coverage-evidence-dot missing"></span> 缺失 {missing}</div>
    </div>
  </div>
</div>
'''

    missing_ev = detail.get("missing_evidence") or []
    missing_html = ""
    if missing_ev:
        miss_items = []
        for me in missing_ev:
            imp = me.get("importance") or "中等"
            imp_class = "high" if imp == "重要" else ("medium" if imp == "中等" else "low")
            miss_items.append(
                f'<div class="coverage-missing-item">'
                f'<span>{escape(me.get("gap_title") or "")}</span>'
                f'<span class="coverage-missing-importance {imp_class}">{escape(imp)}</span>'
                f'</div>'
            )
        missing_html = f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">缺失证据 ({len(missing_ev)}项)</div>
  <div class="coverage-missing-list">{"".join(miss_items)}</div>
</div>
'''

    related_topics = detail.get("related_topics") or []
    related_companies = detail.get("related_companies") or []
    related_html = ""
    if related_topics:
        chips = "".join(f'<span class="coverage-chip">{escape(t)}</span>' for t in related_topics if t)
        related_html += f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">相关主题</div>
  <div class="coverage-chips">{chips}</div>
</div>
'''
    if related_companies:
        chips = "".join(f'<span class="coverage-chip">{escape(c)}</span>' for c in related_companies if c)
        related_html += f'''
<div class="coverage-detail-section">
  <div class="coverage-detail-section-title">关联公司</div>
  <div class="coverage-chips">{chips}</div>
</div>
'''

    return f'''
<div class="coverage-detail-panel">
  <div class="coverage-detail-header">
    <span class="coverage-detail-name">{name}</span>
    <div class="coverage-detail-badges">{badges_html}</div>
  </div>
  {focus_html}
  {signals_html}
  {evidence_html}
  {missing_html}
  {related_html}
</div>
'''


def _render_coverage_distribution(distribution: list[dict]) -> str:
    if not distribution:
        return '''
<div class="coverage-distribution-panel">
  <div class="coverage-table-title" style="margin-bottom:12px">覆盖分布</div>
  <div class="coverage-empty-state">暂无覆盖分布</div>
</div>
'''

    company_pct = next((d["percentage"] for d in distribution if d["type"] == "公司"), 0)
    theme_pct = next((d["percentage"] for d in distribution if d["type"] == "主题"), 0)
    d_company = int(company_pct / 100 * 360)
    d_theme = int((company_pct + theme_pct) / 100 * 360)

    legend_items = []
    for d in distribution:
        typ = d["type"]
        dot_class = {"公司": "company", "主题": "theme", "行业": "industry"}.get(typ, "company")
        legend_items.append(
            f'<div class="coverage-distribution-legend-item">'
            f'<span class="coverage-distribution-dot {dot_class}"></span>'
            f'<span>{escape(typ)} {d["count"]} ({d["percentage"]}%)</span>'
            f'</div>'
        )

    return f'''
<div class="coverage-distribution-panel">
  <div class="coverage-table-title" style="margin-bottom:12px">覆盖分布</div>
  <div class="coverage-distribution-content">
    <div class="coverage-distribution-donut" style="--d-company:{d_company}deg;--d-theme:{d_theme}deg;"></div>
    <div class="coverage-distribution-legend">{"".join(legend_items)}</div>
  </div>
</div>
'''


def _render_priority_hotzone(hotzone: list[dict]) -> str:
    if not hotzone:
        return '''
<div class="priority-hotzone-panel">
  <div class="coverage-table-title" style="margin-bottom:12px">优先级热区</div>
  <div class="coverage-empty-state">暂无高优先级对象</div>
</div>
'''

    cards = []
    for item in hotzone:
        name = escape(item.get("name") or "")
        ev_pct = item.get("evidence_completeness", 0)
        updated = escape(item.get("updated_at") or "")
        cards.append(
            f'<div class="hotzone-card">'
            f'<div class="hotzone-card-name">{name}</div>'
            f'<div class="hotzone-card-meta">证据完整度 · {ev_pct}%</div>'
            f'<div class="hotzone-card-meta">{updated}</div>'
            f'<div class="hotzone-card-progress"><div class="hotzone-card-progress-bar" style="width:{ev_pct}%"></div></div>'
            f'</div>'
        )

    return f'''
<div class="priority-hotzone-panel">
  <div class="coverage-table-title" style="margin-bottom:12px">优先级热区（高优先级对象）</div>
  <div class="priority-hotzone-grid">{"".join(cards)}</div>
</div>
'''


def render_coverage_pool(state: dict, refresh_seconds: int, filters: dict | None = None) -> str:
    view = build_coverage_pool_view_model(state, filters=filters)
    metrics = view["metrics"]
    clean_filters = view["filters"]
    coverage_items = view["coverage_items"]
    selected_detail = view["selected_detail"]
    distribution = view["coverage_distribution"]
    hotzone = view["priority_hotzone"]
    pagination = view["pagination"]
    empty = view["empty_state"]

    metrics_html = _render_coverage_metrics(metrics)
    table_html = _render_coverage_table(coverage_items, empty, clean_filters, pagination)
    detail_html = _render_coverage_detail(selected_detail)
    distribution_html = _render_coverage_distribution(distribution)
    hotzone_html = _render_priority_hotzone(hotzone)

    body = f"""
{metrics_html}
<div class="coverage-layout">
  {table_html}
  <aside class="coverage-side">
    {detail_html}
  </aside>
</div>
<div class="coverage-bottom">
  {distribution_html}
  {hotzone_html}
</div>
<div class="coverage-disclaimer">
  系统展示覆盖状态与证据完整度，不直接给出投资建议。不提供任何投资建议。
</div>
"""

    return render_shell(
        page_title="覆盖池 · 同行资本投研系统",
        current_path="/coverage",
        hero_title="覆盖池",
        hero_subtitle="系统当前覆盖的公司、行业、主题及其研究状态",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def render_placeholder_coverage(state: dict, refresh_seconds: int) -> str:
    return render_placeholder_page(
        "覆盖池",
        "查看当前系统正在覆盖的公司、行业和主题",
        "/coverage",
        state,
        refresh_seconds,
    )


def render_placeholder_signals(state: dict, refresh_seconds: int) -> str:
    return render_placeholder_page(
        "信号流",
        "最新证据时间线与来源追溯",
        "/signals",
        state,
        refresh_seconds,
    )


def _render_research_metrics(metrics: dict) -> str:
    cards = [
        ("research_topic_count", "📁", "blue"),
        ("high_priority_count", "⭐", "orange"),
        ("evidence_gap_count", "📝", "yellow"),
        ("new_today_count", "➕", "green"),
    ]
    html = ""
    for key, icon, tone in cards:
        m = metrics.get(key, {"count": 0, "subtitle": ""})
        html += f"""
<div class="research-metric-card">
  <div class="research-metric-icon {tone}">{icon}</div>
  <div>
    <div class="research-metric-number">{m.get('count', 0)}</div>
    <div class="research-metric-subtitle">{escape(m.get('subtitle', ''))}</div>
  </div>
</div>
"""
    return f'<div class="research-metrics">{html}</div>'


def _render_research_filters(filters: dict) -> str:
    priority_options = [("all", "全部"), ("高", "高"), ("中", "中"), ("低", "低")]
    status_options = [
        ("all", "全部"),
        ("研究中", "研究中"),
        ("初步研究", "初步研究"),
        ("待验证", "待验证"),
        ("证据收集中", "证据收集中"),
        ("暂缓", "暂缓"),
        ("已驳回", "已驳回"),
        ("已通过", "已通过"),
    ]
    sort_options = [
        ("latest", "最新更新"),
        ("priority", "优先级"),
        ("gaps", "缺口最多"),
        ("evidence", "证据最多"),
    ]

    def _options(opts, current):
        return "".join(
            f'<option value="{escape(v)}"{" selected" if v == current else ""}>{escape(l)}</option>'
            for v, l in opts
        )

    return f"""
<div class="research-filters">
  <select class="research-filter-select" name="priority" onchange="this.form.submit()">
    {_options(priority_options, filters.get('priority', 'all'))}
  </select>
  <select class="research-filter-select" name="status" onchange="this.form.submit()">
    {_options(status_options, filters.get('status', 'all'))}
  </select>
  <select class="research-filter-select" name="sort" onchange="this.form.submit()">
    {_options(sort_options, filters.get('sort', 'latest'))}
  </select>
</div>
"""


def _priority_badge_class(priority: str) -> str:
    if priority == "高":
        return "priority-high"
    if priority == "中":
        return "priority-medium"
    return "priority-low"


def _status_badge_class(status: str) -> str:
    if status == "研究中":
        return "status-researching"
    if status == "待验证":
        return "status-pending"
    if status == "证据收集中":
        return "status-gathering"
    if status == "暂缓":
        return "status-deferred"
    if status == "已通过":
        return "status-approved"
    if status == "已驳回":
        return "status-rejected"
    return "status-researching"


def _render_research_item(item: dict, is_selected: bool = False) -> str:
    title = escape(item.get("title") or "")
    rank = item.get("rank", 0)
    priority = item.get("priority") or ""
    status = item.get("status") or ""
    evidence_count = item.get("evidence_count", 0)
    gap_count = item.get("gap_count", 0)
    updated_at = escape(item.get("updated_at") or "")
    short_reason = escape(item.get("short_reason") or "")

    entity_badges = "".join(
        f'<span class="research-item-badge entity">{escape(e)}</span>'
        for e in (item.get("related_entities") or [])
    )
    topic_badges = "".join(
        f'<span class="research-item-badge topic">{escape(t)}</span>'
        for t in (item.get("related_topics") or [])
    )

    selected_cls = " selected" if is_selected else ""

    return f"""
<div class="research-item{selected_cls}" data-item-id="{escape(item.get('item_id', ''))}">
  <div class="research-item-rank">{rank}</div>
  <div class="research-item-content">
    <h4 class="research-item-title">{title}</h4>
    <div class="research-item-badges">
      {entity_badges}
      {topic_badges}
      <span class="research-item-badge {_priority_badge_class(priority)}">{escape(priority)}</span>
      <span class="research-item-badge {_status_badge_class(status)}">{escape(status)}</span>
    </div>
    <p class="research-item-reason">{short_reason}</p>
    <div class="research-item-meta">
      <span>证据 {evidence_count}</span>
      <span>缺口 {gap_count}</span>
      <span>最近更新 {updated_at}</span>
    </div>
  </div>
  <div class="research-item-actions">
    <button class="research-action-btn approve">通过</button>
    <button class="research-action-btn gather">补证据</button>
    <button class="research-action-btn defer">暂缓</button>
    <button class="research-action-btn reject">驳回</button>
  </div>
</div>
"""


def _render_research_list(items: list[dict], empty: bool, filters: dict) -> str:
    header_html = f"""
<div class="research-list-header">
  <div class="research-list-title">研究队列</div>
  <form method="get" action="/research" class="research-filters">
    {_render_research_filters(filters)}
    <input type="hidden" name="q" value="{escape(filters.get('q', ''))}">
  </form>
</div>
"""
    if empty or not items:
        return header_html + """
<div class="research-empty-state">
  <div class="research-empty-state-title">暂无研究队列</div>
  <div>当前没有待深挖主题。请查看信号流或等待系统生成新的证据缺口。</div>
</div>
"""
    list_html = ""
    for idx, item in enumerate(items[:6]):
        list_html += _render_research_item(item, is_selected=(idx == 0))
    return header_html + f"""
<div class="research-list">
  {list_html}
</div>
"""


def _render_research_detail(detail: dict) -> str:
    if not detail.get("title"):
        return """
<div class="research-empty">
  <div class="research-empty-title">请选择研究主题</div>
  <div>当前没有可展示的研究详情。</div>
</div>
"""

    title = escape(detail.get("title") or "")
    priority = detail.get("priority") or ""

    entity_badges = "".join(
        f'<span class="research-item-badge entity">{escape(e)}</span>'
        for e in (detail.get("related_entities") or [])
    )
    topic_badges = "".join(
        f'<span class="research-item-badge topic">{escape(t)}</span>'
        for t in (detail.get("related_topics") or [])
    )

    hypothesis = escape(detail.get("research_hypothesis") or "")
    existing_evidence = "\n".join(
        f"- {escape(e)}" for e in (detail.get("existing_evidence") or [])
    )
    missing_evidence = "\n".join(
        f"- {escape(e)}" for e in (detail.get("missing_evidence") or [])
    )
    next_steps = "\n".join(
        f"- {escape(s)}" for s in (detail.get("next_steps") or [])
    )

    return f"""
<h4 class="research-detail-subtitle">{title}</h4>
<div class="research-detail-badges">
  {entity_badges}
  {topic_badges}
  <span class="research-item-badge {_priority_badge_class(priority)}">{escape(priority)}</span>
</div>
<div class="research-detail-section">
  <h5 class="research-detail-section-title">研究假设</h5>
  <p class="research-detail-text">{hypothesis}</p>
</div>
<div class="research-detail-section">
  <h5 class="research-detail-section-title">已有证据</h5>
  <ul class="research-detail-list">
    {"".join(f'<li>{escape(e)}</li>' for e in (detail.get("existing_evidence") or []))}
  </ul>
</div>
<div class="research-detail-section">
  <h5 class="research-detail-section-title">缺失证据</h5>
  <ul class="research-detail-list">
    {"".join(f'<li>{escape(e)}</li>' for e in (detail.get("missing_evidence") or []))}
  </ul>
</div>
<div class="research-detail-section">
  <h5 class="research-detail-section-title">下一步建议</h5>
  <ul class="research-detail-list">
    {"".join(f'<li>{escape(s)}</li>' for s in (detail.get("next_steps") or []))}
  </ul>
</div>
"""


def _importance_badge_class(importance: str) -> str:
    if importance == "重要":
        return "important"
    if importance == "中等":
        return "medium"
    return "low"


def _render_evidence_gaps(gaps: list[dict]) -> str:
    if not gaps:
        return """
<div class="research-empty" style="padding: 24px 12px;">
  <div class="research-empty-title" style="font-size: 13px;">暂无证据缺口</div>
</div>
"""
    html = ""
    for idx, gap in enumerate(gaps[:4]):
        title = escape(gap.get("gap_title") or "")
        importance = gap.get("importance") or "中等"
        target_source = escape(gap.get("target_source") or "")
        expected_time = escape(gap.get("expected_time") or "")
        html += f"""
<div class="evidence-gap-item">
  <div class="evidence-gap-header">
    <span class="evidence-gap-title-text">{title}</span>
    <span class="evidence-gap-importance {_importance_badge_class(importance)}">{escape(importance)}</span>
  </div>
  <div class="evidence-gap-meta">
    <span>目标来源：{target_source}</span>
    <span>期望时间：{expected_time}</span>
  </div>
</div>
"""
    return f"""
<div class="evidence-gap-title">
  <span>证据缺口</span>
  <a href="#" class="evidence-gap-all-link">全部查看</a>
</div>
<div class="evidence-gap-list">
  {html}
</div>
"""


def render_research_queue(state: dict, refresh_seconds: int, filters: dict | None = None) -> str:
    view = build_research_queue_view_model(state, filters=filters)
    metrics = view["metrics"]
    filters = view["filters"]
    queue_items = view["queue_items"]
    selected_detail = view["selected_detail"]
    evidence_gaps = view["evidence_gaps"]
    empty = view["empty_state"]

    metric_html = _render_research_metrics(metrics)
    list_html = _render_research_list(queue_items, empty, filters)
    detail_html = _render_research_detail(selected_detail)
    gaps_html = _render_evidence_gaps(evidence_gaps)

    body = f"""
{metric_html}
<div class="research-layout">
  <section class="research-list-section">
    {list_html}
  </section>
  <aside class="research-side">
    <div class="research-detail-panel">
      <h3 class="research-detail-title">研究详情</h3>
      {detail_html}
    </div>
    <div class="evidence-gap-panel">
      {gaps_html}
    </div>
  </aside>
</div>
<div class="research-disclaimer">
  系统仅组织研究证据与待办，不直接给出投资建议。不提供任何投资建议。
</div>
"""

    return render_shell(
        page_title="研究队列 · 同行资本投研系统",
        current_path="/research",
        hero_title="研究队列",
        hero_subtitle="待深挖主题管理 / 证据缺口 / 人工决策",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def _render_health_metrics(metrics: dict) -> str:
    def _status_dot(status):
        if status == "正常" or status == "运行正常":
            return '<span class="health-status-dot normal"></span>'
        elif status == "降级" or status == "降级运行":
            return '<span class="health-status-dot degraded"></span>'
        elif status == "阻塞":
            return '<span class="health-status-dot blocked"></span>'
        elif status == "观察中":
            return '<span class="health-status-dot watching"></span>'
        elif status == "待接入":
            return '<span class="health-status-dot pending"></span>'
        else:
            return '<span class="health-status-dot nodata"></span>'

    m1 = metrics.get("market_freshness") or {}
    m2 = metrics.get("source_availability") or {}
    m3 = metrics.get("blocking_issues") or {}
    m4 = metrics.get("evidence_pipeline") or {}

    s1 = m1.get("status", "暂无数据")
    v2 = f'{m2.get("value", 0)}%'
    v3 = f'{m3.get("count", 0)} 项'
    s4 = m4.get("status", "暂无数据")

    cards = f'''
<article class="health-metric-card">
  <div class="health-metric-value">{_status_dot(s1)} 行情新鲜度：{escape(s1)}</div>
  <div class="health-metric-subtitle">{escape(m1.get("subtitle", ""))}</div>
</article>
<article class="health-metric-card">
  <div class="health-metric-value">信息源可用率：{escape(v2)}</div>
  <div class="health-metric-subtitle">{escape(m2.get("subtitle", ""))}</div>
</article>
<article class="health-metric-card">
  <div class="health-metric-value">关键阻塞问题：{escape(v3)}</div>
  <div class="health-metric-subtitle">{escape(m3.get("subtitle", ""))}</div>
</article>
<article class="health-metric-card">
  <div class="health-metric-value">{_status_dot(s4)} 证据流水线：{escape(s4)}</div>
  <div class="health-metric-subtitle">{escape(m4.get("subtitle", ""))}</div>
</article>
'''
    return f'<section class="health-metrics">{cards}</section>'


def _render_health_issue_list(issues: list[dict], empty: bool, filters: dict) -> str:
    if empty or not issues:
        return f'''
<div class="health-issue-section">
  <div class="health-section-header">
    <span class="health-section-title">关键健康问题</span>
  </div>
  <div class="health-empty-state">
    <div class="health-empty-state-title">暂无关键健康问题</div>
    <div>当前未发现影响投研可靠性的阻塞或降级问题。</div>
  </div>
</div>
'''

    items = []
    for issue in issues:
        sev = issue.get("severity", "P2")
        title = escape(issue.get("title", ""))
        scope = escape(issue.get("impact_scope", ""))
        status = issue.get("status", "观察中")
        status_class = {
            "阻塞": "blocked",
            "降级": "degraded",
            "观察中": "watching",
            "已恢复": "resolved",
        }.get(status, "watching")
        desc = escape(issue.get("description", ""))
        update = escape(issue.get("latest_update", ""))
        action = escape(issue.get("action_hint", ""))
        items.append(
            f'<div class="health-issue-item">'
            f'<span class="health-issue-severity {sev}">{sev}</span>'
            f'<div class="health-issue-body">'
            f'<div class="health-issue-top">'
            f'<div class="health-issue-title">{title}</div>'
            f'<span class="health-issue-status {status_class}">{status}</span>'
            f'</div>'
            f'<div class="health-issue-scope">影响范围：{scope}</div>'
            f'<div class="health-issue-desc">{desc}</div>'
            f'<div class="health-issue-meta"><span>最近更新：{update}</span><span>{action}</span></div>'
            f'</div>'
            f'</div>'
        )

    return f'''
<div class="health-issue-section">
  <div class="health-section-header">
    <span class="health-section-title">关键健康问题</span>
  </div>
  <div class="health-issue-list">{"".join(items)}</div>
</div>
'''


def _render_module_health(modules: list[dict]) -> str:
    items = []
    for m in modules:
        name = escape(m.get("module_name", ""))
        status = m.get("status", "暂无数据")
        dot_class = {
            "运行正常": "normal",
            "降级运行": "degraded",
            "阻塞": "blocked",
            "观察中": "watching",
            "待接入": "pending",
        }.get(status, "nodata")
        summary = escape(m.get("summary", ""))
        items.append(
            f'<div class="module-health-item">'
            f'<div class="module-health-left">'
            f'<span class="health-status-dot {dot_class}"></span>'
            f'<span>{name}</span>'
            f'</div>'
            f'<span class="module-health-status">{status}，{summary}</span>'
            f'</div>'
        )

    return f'''
<div class="health-panel">
  <div class="health-panel-title">系统模块健康度</div>
  <div class="module-health-list">{"".join(items)}</div>
</div>
'''


def _render_health_source_distribution(distribution: list[dict]) -> str:
    if not distribution:
        return '''
<div class="health-panel">
  <div class="health-panel-title">数据源状态分布</div>
  <div class="health-empty-state">暂无数据</div>
</div>
'''

    total = sum(d["count"] for d in distribution)
    norm_count = next((d["count"] for d in distribution if d["status"] == "正常"), 0)
    deg_count = next((d["count"] for d in distribution if d["status"] == "降级"), 0)
    blk_count = next((d["count"] for d in distribution if d["status"] == "阻塞"), 0)
    watch_count = next((d["count"] for d in distribution if d["status"] == "观察中"), 0)
    pend_count = next((d["count"] for d in distribution if d["status"] == "待接入"), 0)

    p_norm = int(norm_count / total * 360) if total else 0
    p_deg = int((norm_count + deg_count) / total * 360) if total else 0
    p_blk = int((norm_count + deg_count + blk_count) / total * 360) if total else 0
    p_watch = int((norm_count + deg_count + blk_count + watch_count) / total * 360) if total else 0

    gradient = f'conic-gradient(#059669 0deg {p_norm}deg, #f59e0b {p_norm}deg {p_deg}deg, #dc2626 {p_deg}deg {p_blk}deg, #6366f1 {p_blk}deg {p_watch}deg, #9ca3af {p_watch}deg 360deg)'

    legend_items = []
    status_colors = {
        "正常": "#059669",
        "降级": "#f59e0b",
        "阻塞": "#dc2626",
        "观察中": "#6366f1",
        "待接入": "#9ca3af",
        "暂无数据": "#cbd5e1",
    }
    for d in distribution:
        s = d["status"]
        if d["count"] == 0:
            continue
        color = status_colors.get(s, "#cbd5e1")
        legend_items.append(
            f'<div class="health-legend-item">'
            f'<div class="health-legend-left"><span class="health-legend-dot" style="background:{color}"></span><span>{s}</span></div>'
            f'<span>{d["count"]} ({d["percentage"]}%)</span>'
            f'</div>'
        )

    return f'''
<div class="health-panel">
  <div class="health-panel-title">数据源状态分布</div>
  <div class="health-distribution">
    <div class="health-ring" style="background:{gradient}">
      <div class="health-ring-label">总数 {total}</div>
    </div>
    <div class="health-legend">{"".join(legend_items)}</div>
  </div>
</div>
'''


def _render_run_summary(summary: dict) -> str:
    success = summary.get("successful_batches", 0)
    failed = summary.get("failed_batches", 0)
    pending = summary.get("pending_queue", 0)
    last_check = summary.get("last_check", "未知")

    return f'''
<div class="health-panel">
  <div class="health-panel-title">今日运行摘要</div>
  <div class="run-summary-grid">
    <div class="run-summary-item">
      <div class="run-summary-value">{success}</div>
      <div class="run-summary-label">成功批次</div>
    </div>
    <div class="run-summary-item">
      <div class="run-summary-value" style="color:#dc2626">{failed}</div>
      <div class="run-summary-label">失败批次</div>
    </div>
    <div class="run-summary-item">
      <div class="run-summary-value" style="color:#f59e0b">{pending}</div>
      <div class="run-summary-label">待处理队列</div>
    </div>
    <div class="run-summary-item">
      <div class="run-summary-value" style="font-size:14px">{escape(last_check)}</div>
      <div class="run-summary-label">最近一次检查</div>
    </div>
  </div>
</div>
'''


def render_data_health(state: dict, refresh_seconds: int, filters: dict | None = None) -> str:
    view = build_data_health_view_model(state, filters=filters)
    metrics = view["metrics"]
    clean_filters = view["filters"]
    issues = view["health_issues"]
    modules = view["module_health"]
    distribution = view["source_status_distribution"]
    summary = view["run_summary"]
    empty = view["empty_state"]

    metrics_html = _render_health_metrics(metrics)
    issues_html = _render_health_issue_list(issues, empty, clean_filters)
    module_html = _render_module_health(modules)
    dist_html = _render_health_source_distribution(distribution)
    summary_html = _render_run_summary(summary)

    body = f"""
{metrics_html}
<div class="health-layout">
  {issues_html}
  <aside class="health-side">
    {module_html}
    {dist_html}
    {summary_html}
  </aside>
</div>
<div class="health-disclaimer">
  数据健康页面用于观察投研系统的运行状态与数据质量，帮助及时发现并定位问题，保障研究工作的可靠性与连续性。不提供任何投资建议。
</div>
"""

    return render_shell(
        page_title="数据健康 · 同行资本投研系统",
        current_path="/health",
        hero_title="数据健康",
        hero_subtitle="聚焦影响投研可靠性的关键健康状态",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def render_placeholder_health(state: dict, refresh_seconds: int) -> str:
    return render_placeholder_page(
        "数据健康",
        "影响投研可靠性的关键健康状态",
        "/health",
        state,
        refresh_seconds,
    )


def _render_filter_bar(filters: dict) -> str:
    time_options = [("24h", "近 24 小时"), ("7d", "近 7 天"), ("30d", "近 30 天"), ("all", "全部")]
    source_options = [
        ("all", "全部"),
        ("official_disclosure", "官方披露"),
        ("company_ir", "公司 IR"),
        ("public_research", "公开研究"),
        ("media_excerpt", "媒体摘录"),
        ("earnings_call", "电话会纪要"),
        ("foundation", "Foundation"),
        ("risk_monitor", "风险监控"),
    ]
    entity_options = [("all", "全部"), ("company", "公司"), ("industry", "行业"), ("theme", "主题")]
    strength_options = [("all", "全部"), ("高", "高"), ("中", "中"), ("低", "低"), ("待确认", "待确认")]

    def _options(opts, current):
        return "".join(
            f'<option value="{escape(v)}"{" selected" if v == current else ""}>{escape(l)}</option>'
            for v, l in opts
        )

    return f"""
<div class="signal-filter-bar">
  <div class="filter-group">
    <span class="filter-label">时间范围</span>
    <select class="filter-select" name="time_range" onchange="this.form.submit()">
      {_options(time_options, filters.get('time_range', 'all'))}
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">来源类型</span>
    <select class="filter-select" name="source_type" onchange="this.form.submit()">
      {_options(source_options, filters.get('source_type', 'all'))}
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">关联对象</span>
    <select class="filter-select" name="entity" onchange="this.form.submit()">
      {_options(entity_options, filters.get('entity', 'all'))}
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">证据强度</span>
    <select class="filter-select" name="strength" onchange="this.form.submit()">
      {_options(strength_options, filters.get('strength', 'all'))}
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">关键词搜索</span>
    <input class="filter-input" type="text" name="q" placeholder="输入关键词" value="{escape(filters.get('q', ''))}">
  </div>
  <a class="filter-reset" href="/signals">重置筛选</a>
</div>
"""


def _strength_badge_class(strength: str) -> str:
    if strength == "高":
        return "strength-high"
    if strength == "中":
        return "strength-medium"
    if strength == "低":
        return "strength-low"
    return "strength-unknown"


def _render_signal_card(signal: dict) -> str:
    title = escape(signal.get("title") or "")
    summary = escape(signal.get("summary") or "")
    time_label = escape(signal.get("time_label") or "")
    source_label = escape(signal.get("source_label") or "")
    strength = signal.get("evidence_strength") or "待确认"
    review = signal.get("review_status") or ""

    entity_badges = "".join(
        f'<span class="signal-badge entity">{escape(e)}</span>'
        for e in (signal.get("related_entities") or [])
    )
    topic_badges = "".join(
        f'<span class="signal-badge topic">{escape(t)}</span>'
        for t in (signal.get("related_topics") or [])
    )

    source_url = signal.get("source_url")
    evidence_url = signal.get("evidence_url")
    source_btn = (
        f'<a class="signal-btn" href="{escape(source_url)}" target="_blank">查看原文</a>'
        if source_url
        else '<span class="signal-btn disabled">暂无原文</span>'
    )
    evidence_btn = (
        f'<a class="signal-btn" href="{escape(evidence_url)}" target="_blank">查看证据包</a>'
        if evidence_url
        else '<span class="signal-btn disabled">暂无证据包</span>'
    )

    review_badge = f'<span class="signal-badge review">{escape(review)}</span>' if review else ""

    return f"""
<div class="timeline-item">
  <div class="timeline-node"></div>
  <div class="timeline-time">{time_label}</div>
  <div class="signal-card">
    <h3 class="signal-title">{title}</h3>
    <p class="signal-summary">{summary}</p>
    <div class="signal-badges">
      <span class="signal-badge source">{source_label}</span>
      {entity_badges}
      {topic_badges}
      <span class="signal-badge {_strength_badge_class(strength)}">{escape(strength)}</span>
      {review_badge}
    </div>
    <div class="signal-actions">
      {source_btn}
      {evidence_btn}
    </div>
  </div>
</div>
"""


def _render_timeline(signals: list[dict], empty: bool) -> str:
    if empty or not signals:
        return """
<div class="signal-empty">
  <div class="signal-empty-title">暂无信号</div>
  <div class="signal-empty-desc">当前筛选条件下没有可展示的证据或事件。请调整筛选条件，或查看数据健康。</div>
</div>
"""
    items = "".join(_render_signal_card(s) for s in signals)
    load_more = (
        """
<div class="load-more">
  <span class="load-more-btn">加载更多 ▾</span>
</div>
"""
        if len(signals) >= 8
        else ""
    )
    return f'<div class="timeline">{items}</div>{load_more}'


def _render_summary_stats(summary: dict) -> str:
    cards = [
        ("total_signals", "今日新增信号数", "📄", "blue"),
        ("focus_company_count", "重点公司数", "🏢", "purple"),
        ("high_strength_count", "高强度证据数", "🛡", "red"),
        ("needs_review_count", "需复核数", "📋", "amber"),
    ]
    html = ""
    for key, label, icon, tone in cards:
        count = summary.get(key, 0)
        html += f"""
<div class="summary-stat">
  <div class="summary-icon {tone}">{icon}</div>
  <div>
    <div class="summary-number">{count}</div>
    <div class="summary-label">{label}</div>
  </div>
</div>
"""
    return f'<div class="signal-summary-grid">{html}</div>'


def _render_hot_entities(entities: list[dict]) -> str:
    if not entities:
        return """
<div class="signal-empty" style="padding: 24px 12px;">
  <div class="signal-empty-title" style="font-size: 13px;">暂无热门关联对象</div>
</div>
"""
    chips = ""
    for e in entities:
        name = escape(e.get("name") or "")
        etype = e.get("type") or "company"
        cls = "hot-chip theme" if etype == "theme" else "hot-chip"
        chips += f'<span class="{cls}">{name}</span>'
    return f'<div class="hot-chips">{chips}</div>'


def _render_source_distribution(distribution: list[dict]) -> str:
    if not distribution or all(d.get("count", 0) == 0 for d in distribution):
        return """
<div class="signal-empty" style="padding: 24px 12px;">
  <div class="signal-empty-title" style="font-size: 13px;">暂无来源分布数据</div>
</div>
"""
    bars = ""
    for d in distribution:
        label = escape(d.get("label") or "")
        count = d.get("count", 0)
        pct = d.get("pct", 0)
        bars += f"""
<div class="source-bar-item">
  <span class="source-bar-label">{label}</span>
  <div class="source-bar-track">
    <div class="source-bar-fill" style="width: {pct}%;"></div>
  </div>
  <span class="source-bar-count">{count}</span>
</div>
"""
    return f"""
<div class="source-bar-list">
  {bars}
</div>
<div class="source-bar-unit">单位：条</div>
"""


def render_signal_flow(state: dict, refresh_seconds: int, filters: dict | None = None) -> str:
    view = build_signal_flow_view_model(state, filters=filters)
    clean_filters = view["filters"]
    summary = view["summary"]
    signals = view["signals"]
    hot_entities = view["hot_entities"]
    source_dist = view["source_distribution"]
    empty = view["empty_state"]

    filter_bar = _render_filter_bar(clean_filters)
    timeline = _render_timeline(signals, empty)
    stats = _render_summary_stats(summary)
    hot = _render_hot_entities(hot_entities)
    source_bars = _render_source_distribution(source_dist)

    body = f"""
{filter_bar}
<div class="signal-layout">
  <article class="timeline-section">
    <h2 class="section-title">信号时间线</h2>
    {timeline}
  </article>
  <aside class="signal-side">
    <div class="side-panel">
      <h3 class="side-title">今日信号摘要</h3>
      {stats}
    </div>
    <div class="side-panel">
      <h3 class="side-title">热门关联对象</h3>
      {hot}
    </div>
    <div class="side-panel">
      <h3 class="side-title">信号来源分布</h3>
      {source_bars}
    </div>
  </aside>
</div>
<div class="signal-disclaimer">
  系统仅展示证据与信号，不直接给出投资建议。不提供任何投资建议。
</div>
"""

    return render_shell(
        page_title="信号流 · 同行资本投研系统",
        current_path="/signals",
        hero_title="信号流",
        hero_subtitle="最新证据时间线与来源追溯",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        **shell_state_kwargs(state),
    )


def render_operations_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    reporting = state.get("reporting") or {}
    analysis_forecast = state.get("analysis_forecast") or {}
    capital = state.get("capital_flow") or {}
    operations = state.get("operations") or {}
    scheduler = operations.get("scheduler") or {}
    run_log = operations.get("run_log") or {}
    latest_run = scheduler.get("latest_run") or {}
    latest_by_job = scheduler.get("latest_by_job") or {}
    latest_report_date = reporting.get("report_surface_date") or overview.get("latest_daily_report_date") or "-"
    scheduler_counts = scheduler.get("today_status_counts") or {}
    latest_run_label = latest_run.get("label") or latest_run.get("job_id") or "暂无"
    latest_run_time = latest_run.get("finished_at") or latest_run.get("started_at") or "-"
    latest_run_steps = latest_run.get("command_count") or 0
    latest_run_footer = (
        link_for_rel_path(latest_run.get("summary_rel_path"), "查看最新自动链摘要")
        if latest_run.get("summary_rel_path")
        else "<span class='muted'>当前没有最新自动链摘要入口。</span>"
    )

    metrics = [
        {
            "title": "今日自动链",
            "value": f"{scheduler.get('today_run_count') or 0} 次",
            "note": "按业务链口径统计今天已经完成的批次。",
            "tone": "good" if (scheduler.get("today_run_count") or 0) > 0 else "warning",
            "footer_html": render_count_badges(scheduler_counts, "今天还没有自动链记录"),
        },
        {
            "title": "最新完成链",
            "value": latest_run_label,
            "note": f"{latest_run_time} · {fmt_number(latest_run_steps)} 步",
            "tone": status_tone(latest_run.get("status")),
            "footer_html": latest_run_footer,
        },
        {
            "title": "价格区间推演",
            "value": analysis_forecast.get("created_at") or "-",
            "note": (
                f"已覆盖个股 {fmt_number(analysis_forecast.get('equity_count') or 0)} 只 / "
                f"指数代理 {fmt_number(analysis_forecast.get('index_proxy_count') or 0)} 条。"
            ),
            "tone": "good" if analysis_forecast.get("created_at") else "warning",
            "footer_html": link_for_artifact(analysis_forecast.get("artifact")),
        },
        {
            "title": "A股底层行情",
            "value": overview.get("a_share_trade_date") or "-",
            "note": (
                f"页面实时锚点 {overview.get('a_share_expected_trade_date') or '-'} · "
                f"{fmt_lag_days(overview.get('a_share_expected_gap_days'))}"
            ),
            "tone": "good" if (overview.get("a_share_expected_gap_days") or 0) == 0 else "warning",
        },
        {
            "title": "港股底层行情",
            "value": overview.get("hk_trade_date") or "-",
            "note": (
                f"页面实时锚点 {overview.get('hk_expected_trade_date') or '-'} · "
                f"{fmt_lag_days(overview.get('hk_expected_gap_days'))}"
            ),
            "tone": "good" if (overview.get("hk_expected_gap_days") or 0) == 0 else "warning",
        },
        {
            "title": "美股底层行情",
            "value": overview.get("us_trade_date") or "-",
            "note": (
                f"页面实时锚点 {overview.get('us_expected_trade_date') or '-'} · "
                f"{fmt_lag_days(overview.get('us_expected_gap_days'))}"
            ),
            "tone": "good" if (overview.get("us_expected_gap_days") or 0) == 0 else "warning",
        },
    ]

    operation_rows = []
    for job in OPERATIONS_BLUEPRINT:
        latest_job_run = latest_by_job.get(job["job_id"]) or {}
        operation_rows.append(
            [
                f"<strong>{escape(job['label'])}</strong><div class='muted' style='margin-top:8px'>{escape(job['schedule_note'])}</div>",
                escape(job["time_text"]),
                escape(job["frequency_text"]),
                escape(job["purpose_text"]),
                escape(job["deliverable_text"]),
                render_operation_run_cell(latest_job_run),
            ]
        )

    recent_run_rows = []
    for item in (scheduler.get("recent_runs") or [])[:10]:
        recent_run_rows.append(
            [
                escape(item.get("finished_at") or item.get("started_at") or "-"),
                f"<strong>{escape(item.get('label') or item.get('job_id') or '-')}</strong>",
                render_badge_group(
                    [
                        (item.get("status"), status_tone(item.get("status"))),
                        (f"{item.get('command_count') or 0} 步", "ghost"),
                    ]
                ),
                escape(str(item.get("failed_count") or 0)),
                link_for_rel_path(item.get("summary_rel_path"), "查看运行摘要"),
            ]
        )

    recent_script_rows = []
    for item in (run_log.get("recent_entries") or [])[:12]:
        recent_script_rows.append(
            [
                escape(item.get("time") or "-"),
                f"<code>{escape(item.get('script') or '-')}</code>",
                badge(item.get("status"), status_tone(item.get("status"))),
                escape(compact_text(item.get("message") or "-", 72)),
                link_for_rel_path(item.get("summary_rel_path"), "查看产物") if item.get("summary_rel_path") else "<span class='muted'>无单独产物</span>",
            ]
        )

    margin_balance = capital.get("margin_balance") or {}
    stock_connect = capital.get("stock_connect") or {}
    data_gap_rows = [
        [
            "A股行情",
            escape(overview.get("a_share_expected_trade_date") or "-"),
            escape(overview.get("a_share_trade_date") or "-"),
            escape(fmt_lag_days(overview.get("a_share_expected_gap_days"))),
            escape(
                f"页面按 {overview.get('a_share_expected_trade_date') or '-'} 实时锚点展示，底层最近可复核日 {overview.get('a_share_trade_date') or '-'}。"
            ),
        ],
        [
            "港股行情",
            escape(overview.get("hk_expected_trade_date") or "-"),
            escape(overview.get("hk_trade_date") or "-"),
            escape(fmt_lag_days(overview.get("hk_expected_gap_days"))),
            escape(
                f"页面按 {overview.get('hk_expected_trade_date') or '-'} 实时锚点展示，底层最近可复核日 {overview.get('hk_trade_date') or '-'}。"
            ),
        ],
        [
            "美股行情",
            escape(overview.get("us_expected_trade_date") or "-"),
            escape(overview.get("us_trade_date") or "-"),
            escape(fmt_lag_days(overview.get("us_expected_gap_days"))),
            escape(
                f"页面按 {overview.get('us_expected_trade_date') or '-'} 实时锚点展示，底层最近可复核日 {overview.get('us_trade_date') or '-'}。"
            ),
        ],
        [
            "两融",
            escape(margin_balance.get("requested_anchor_trade_date") or "-"),
            escape(margin_balance.get("anchor_trade_date") or "-"),
            escape(fmt_lag_days(iso_date_gap_days(margin_balance.get("requested_anchor_trade_date"), margin_balance.get("anchor_trade_date")))),
            escape(relabel_live_copy(margin_balance.get("metric_note") or margin_balance.get("fact_summary_line") or "-")),
        ],
        [
            "互联互通日频",
            escape(stock_connect.get("requested_anchor_trade_date") or "-"),
            escape(stock_connect.get("anchor_trade_date") or "-"),
            escape(fmt_lag_days(iso_date_gap_days(stock_connect.get("requested_anchor_trade_date"), stock_connect.get("anchor_trade_date")))),
            escape(relabel_live_copy(stock_connect.get("metric_note") or stock_connect.get("fact_summary_line") or "-")),
        ],
        [
            "今日日报口径",
            escape(overview.get("today") or "-"),
            escape(latest_report_date),
            escape(fmt_lag_days(overview.get("daily_report_lag_days"))),
            escape(
                "日报页当前会优先展示和今天业务面最贴近的候选版；正式日报还没完全跟上时，也会明确标出来。"
            ),
        ],
    ]

    freshness_warning = run_log.get("freshness_warning")
    warning_html = (
        "<article class='panel'>"
        "<h2>运行提醒</h2>"
        f"<div class='section-intro'>{escape(freshness_warning)}</div>"
        "</article>"
        if freshness_warning
        else ""
    )

    body = (
        "<section class='panel'>"
        "<h2>今天这套系统跑到了哪</h2>"
        "<div class='section-intro'>这里不讲底层实现，只回答三件事：今天跑了几条链、最新一条是什么、关键数据新不新。</div>"
        f"{render_metric_grid(metrics)}"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>岗位节奏</h2>"
        "<div class='section-intro'>把每天固定要跑的业务岗位按时间顺序摊开，方便直接核对谁负责什么、交付到哪里。</div>"
        f"{render_html_table(['岗位 / 链路', '计划时间', '频次', '主要工作', '交付去向', '最近一次运行'], operation_rows, '当前还没有岗位定义。')}"
        "</article>"
        "<article class='panel'>"
        "<h2>今天已经跑出来什么</h2>"
        "<div class='section-intro'>这里看今天最近几条自动链的真实运行结果，不看设计稿，只看已经发生的业务动作。</div>"
        f"{render_html_table(['完成时间', '链路', '状态', '失败步数', '运行摘要'], recent_run_rows, '今天还没有自动链运行记录。')}"
        "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>当前数据还差在哪</h2>"
        "<div class='section-intro'>页面可以按实时锚点展示，但底层事实库没跟上时要明确揭示，不能把缺口藏起来。</div>"
        f"{render_html_table(['数据维度', '页面锚点 / 请求日', '底层 / 官方最新日', '差距', '当前说明'], data_gap_rows, '当前没有数据缺口信息。')}"
        "</article>"
        "<article class='panel'>"
        "<h2>脚本层最近记录</h2>"
        "<div class='section-intro'>这一栏是自动链背后的最近脚本记录，方便快速核对今天到底新生成了哪些业务产物。</div>"
        f"{render_html_table(['时间', '脚本', '结果', '一句话', '产物入口'], recent_script_rows, '今天还没有脚本层记录。')}"
        "</article>"
        "</section>"
        f"{warning_html}"
    )

    return render_shell(
        page_title="SMR 自动运营",
        current_path="/operations",
        hero_title="自动运营",
        hero_subtitle="把每天哪些岗位在什么时候跑、今天已经交付了什么、哪些关键数据还不够新，集中放在一页里。",
        hero_facts=[
            ("今日自动链", f"{scheduler.get('today_run_count') or 0} 次"),
            ("最新完成链", latest_run_label),
            ("价格区间推演", analysis_forecast.get("created_at") or "-"),
            ("当前日报口径", latest_report_date),
        ],
        body=body,
        refresh_seconds=refresh_seconds,
        **shell_state_kwargs(state),
    )


def render_reports_page(state: dict, refresh_seconds: int) -> str:
    overview = state["overview"]
    reporting = state["reporting"]
    analysis_forecast = state.get("analysis_forecast") or {}
    capital = state["capital_flow"]
    generated_at = state.get("generated_at")
    portfolio = state["portfolio_action"]
    risk_decision = ((state.get("risk") or {}).get("decision") or {})
    scheduler = ((state.get("operations") or {}).get("scheduler") or {})
    latest_run = scheduler.get("latest_run") or {}
    detail_enabled_codes = {item.get("ts_code") for item in iter_unique_watch_items(state) if item.get("ts_code")}
    latest_report_is_aligned = bool(reporting.get("latest_report_is_aligned"))
    report_surface_date = reporting.get("report_surface_date") or overview.get("latest_daily_report_date")
    latest_report_anchor_date = reporting.get("latest_report_anchor_date") or overview.get("latest_daily_report_date")
    active_report_artifact = reporting.get("latest_report")
    report_title = reporting.get("latest_report_title") or "当前暂无日报"
    report_summary = rewrite_report_live_header(
        reporting.get("latest_report_summary"),
        overview,
        capital,
        generated_at,
    ) or "当前还没有提取到日报摘要。"
    report_mode_note = "当前正式日报已经和今天业务面完成对齐。"
    if not latest_report_is_aligned and reporting.get("daily_candidate"):
        active_report_artifact = reporting.get("daily_candidate")
        report_title = f"SMR 当日候选版 | {report_surface_date or '-'}"
        report_summary = rewrite_report_live_header(
            reporting.get("daily_candidate_summary"),
            overview,
            capital,
            generated_at,
        ) or report_summary
        report_mode_note = (
            f"正式日报还停在 {latest_report_anchor_date or '-'}，当前先展示 {report_surface_date or '-'} 候选版。"
        )
    report_body = rewrite_report_live_header(read_artifact_text(active_report_artifact), overview, capital, generated_at)
    external_research_items = ((reporting.get("external_research_digest") or {}).get("items") or [])[:7]
    official_material_items = ((reporting.get("official_material_digest") or {}).get("items") or [])[:7]
    public_transcript_items = ((reporting.get("public_transcript_digest") or {}).get("items") or [])[:7]
    public_signal_items = ((reporting.get("public_analyst_signal_digest") or {}).get("items") or [])[:7]
    market_flow = reporting.get("market_flow_anomaly") or {}
    market_flow_coverage = market_flow.get("coverage_summary") or {}
    market_flow_overview_lines = market_flow.get("overview_lines") or []
    market_flow_a_items = (market_flow.get("markets") or {}).get("A") or []
    market_flow_h_items = (market_flow.get("markets") or {}).get("H") or []
    market_flow_us_items = (market_flow.get("markets") or {}).get("US") or []
    forecast_focus_items = sorted(
        analysis_forecast.get("all_equities") or [],
        key=lambda item: (
            -(abs((item.get("next_day") or {}).get("bias_pct") or 0)),
            -((item.get("confidence") or 0)),
        ),
    )[:3]
    forecast_overview_html = "".join(
        f"<li>{escape(business_text(item))}</li>" for item in (analysis_forecast.get("overview_lines") or [])[:5]
    ) or "<li>当前还没有价格区间推演摘要。</li>"
    forecast_focus_rows = []
    for item in forecast_focus_items:
        forecast_focus_rows.append(
            [
                render_analysis_subject(item, state),
                render_badge_group([(item.get("bias_label"), "neutral"), (item.get("confidence_label"), "ghost")]),
                escape(fmt_forecast_window(item.get("next_day"))),
                escape(fmt_forecast_window(item.get("five_day"))),
                escape(forecast_driver_summary(item, 84)),
            ]
        )
    primary_calls = "".join(f"<li>{escape(live_business_text(item))}</li>" for item in (portfolio.get("primary_call") or []))
    if not primary_calls:
        primary_calls = "<li>当前没有抽取到新的业务主张。</li>"
    market_flow_overview_html = "".join(
        f"<li>{escape(business_text(item))}</li>" for item in market_flow_overview_lines
    ) or "<li>当前还没有抽取到跨市场异动结论。</li>"
    current_state = state.get("current_state") or {}
    evidence_counts = (current_state.get("status_counts") or {}).get("evidence") or {}
    paper_counts = (current_state.get("status_counts") or {}).get("paper_watch") or {}
    evidence_gap_count = len(current_state.get("evidence_gaps") or [])
    paper_watch_count = len(current_state.get("paper_watch") or [])
    top_opportunity_rows = []
    for item in (current_state.get("top_opportunities") or [])[:5]:
        risk_text = compact_text((item.get("risks") or [""])[0], 72)
        next_check = compact_text((item.get("next_checks") or [""])[0], 82)
        top_opportunity_rows.append(
            [
                render_watch_name_link({"ts_code": item.get("ts_code"), "name": item.get("name")}),
                escape(fmt_number(item.get("opportunity_score"))),
                badge(item.get("radar_bucket"), status_tone(item.get("radar_bucket"))),
                escape(risk_text or "-"),
                escape(next_check or "-"),
            ]
        )
    risk_points = []
    for value in (risk_decision.get("headline_actions") or [])[:3]:
        if value:
            risk_points.append(live_business_text(value))
    for value in (risk_decision.get("portfolio_constraints") or [])[:3]:
        if value:
            risk_points.append(live_business_text(value))
    risk_points_html = "".join(f"<li>{escape(item)}</li>" for item in risk_points[:5]) or "<li>当前没有抽取到额外风险约束。</li>"
    conclusion_metrics = [
        {
            "title": "当前组合口径",
            "value": risk_decision.get("portfolio_state_label") or code_label(risk_decision.get("portfolio_state")) or "-",
            "note": compact_text(
                live_business_text(risk_decision.get("portfolio_sell_call") or risk_decision.get("portfolio_buy_call") or "-"),
                76,
            ),
            "tone": status_tone(risk_decision.get("portfolio_state")),
        },
        {
            "title": "证据缺口",
            "value": f"{evidence_gap_count} 个",
            "note": "高分机会的新鲜公开来源已经补齐。" if evidence_gap_count == 0 else "先补来源，再判断是否升级。",
            "tone": "good" if evidence_gap_count == 0 else "warning",
            "footer_html": render_count_badges(evidence_counts, "暂无证据分布"),
        },
        {
            "title": "纸面观察",
            "value": f"{paper_watch_count} 张",
            "note": "只做模拟跟踪，不构成真实交易指令。",
            "tone": "neutral",
            "footer_html": render_count_badges(paper_counts, "暂无纸面观察状态"),
        },
        {
            "title": "动作建议",
            "value": fmt_number(portfolio.get("action_count") or 0),
            "note": compact_text(live_business_text((portfolio.get("primary_call") or [""])[0]), 76),
            "tone": status_tone(portfolio.get("execution_precheck_status")),
        },
    ]

    latest_run_label = latest_run.get("label") or latest_run.get("job_id") or "暂无"
    latest_run_time = latest_run.get("finished_at") or latest_run.get("started_at") or "-"
    scheduler_counts = scheduler.get("today_status_counts") or {}
    latest_run_link_html = (
        f"<div class='story-footer' style='margin-top:12px'>{link_for_rel_path(latest_run.get('summary_rel_path'), '查看最新自动链摘要')}</div>"
        if latest_run.get("summary_rel_path")
        else ""
    )
    a_expected = overview.get("a_share_expected_trade_date") or overview.get("a_share_trade_date") or "-"
    hk_expected = overview.get("hk_expected_trade_date") or overview.get("hk_trade_date") or "-"
    us_expected = overview.get("us_expected_trade_date") or overview.get("us_trade_date") or "-"
    a_fact = overview.get("a_share_trade_date") or "-"
    hk_fact = overview.get("hk_trade_date") or "-"
    us_fact = overview.get("us_trade_date") or "-"
    a_gap = overview.get("a_share_expected_gap_days")
    hk_gap = overview.get("hk_expected_gap_days")
    us_gap = overview.get("us_expected_gap_days")
    a_note = (
        "实时锚点已和底层行情库对齐。"
        if a_fact == a_expected
        else f"页面按 {a_expected} 实时锚点展示，底层行情库最近可复核日 {a_fact}。"
    )
    hk_note = (
        "实时锚点已和底层行情库对齐。"
        if hk_fact == hk_expected
        else f"页面按 {hk_expected} 实时锚点展示，底层行情库最近可复核日 {hk_fact}。"
    )
    us_note = (
        "实时锚点已和底层行情库对齐。"
        if us_fact == us_expected
        else f"页面按 {us_expected} 实时锚点展示，底层行情库最近可复核日 {us_fact}。"
    )
    report_metric_note = (
        "正式日报已经和今天业务面同步。"
        if latest_report_is_aligned
        else f"正式日报还停在 {latest_report_anchor_date or '-'}，当前优先展示候选版。"
    )
    metrics = [
        {
            "title": "A股实时锚点",
            "value": a_expected,
            "note": a_note,
            "tone": "good" if a_gap == 0 else "warning",
        },
        {
            "title": "港股实时锚点",
            "value": hk_expected,
            "note": hk_note,
            "tone": "good" if hk_gap == 0 else "warning",
        },
        {
            "title": "美股实时锚点",
            "value": us_expected,
            "note": us_note,
            "tone": "good" if us_gap == 0 else "warning",
        },
        {
            "title": "当前日报口径",
            "value": report_surface_date or "-",
            "note": report_metric_note,
            "tone": "good" if latest_report_is_aligned else "warning",
        },
        {
            "title": "两融随时",
            "value": capital["margin_balance"].get("anchor_trade_date") or "-",
            "note": compact_text(relabel_live_copy(capital["margin_balance"].get("metric_note")), 72),
            "tone": "good" if capital["margin_balance"].get("anchor_trade_date") else "warning",
        },
        {
            "title": "互联互通随时",
            "value": capital["stock_connect"].get("anchor_trade_date") or "-",
            "note": compact_text(relabel_live_copy(capital["stock_connect"].get("metric_note")), 72),
            "tone": "good" if capital["stock_connect"].get("anchor_trade_date") else "warning",
        },
        {
            "title": "最新自动链",
            "value": latest_run_label,
            "note": f"{latest_run_time} / 最近一次完成链路",
            "tone": status_tone(latest_run.get("status")),
            "footer_html": render_badge_group(
                [
                    (latest_run.get("status"), status_tone(latest_run.get("status"))),
                    (f"{latest_run.get('command_count') or 0} 步", "ghost"),
                ]
            ),
        },
        {
            "title": "今日自动链",
            "value": f"{scheduler.get('today_run_count') or 0} 次",
            "note": "按调度链维度统计今天已经完成的业务批次。",
            "tone": "neutral",
            "footer_html": render_count_badges(scheduler_counts, "今天还没有自动链运行记录"),
        },
        {
            "title": "组合状态",
            "value": risk_decision.get("portfolio_state_label") or code_label(risk_decision.get("portfolio_state")) or "-",
            "note": compact_text(
                business_text(risk_decision.get("portfolio_sell_call") or risk_decision.get("portfolio_buy_call") or "-"),
                56,
            ),
            "tone": status_tone(risk_decision.get("portfolio_state")),
        },
        {
            "title": "买入候选",
            "value": fmt_number(risk_decision.get("buy_candidate_count") or 0),
            "note": "当前能形成可读买入风控结论的标的数量。",
            "tone": "good" if (risk_decision.get("buy_candidate_count") or 0) > 0 else "ghost",
        },
        {
            "title": "卖出候选",
            "value": fmt_number(risk_decision.get("sell_candidate_count") or 0),
            "note": "当前需要先处理或继续复核的卖出侧对象数量。",
            "tone": "warning" if (risk_decision.get("sell_candidate_count") or 0) > 0 else "good",
        },
        {
            "title": "动作建议",
            "value": fmt_number(portfolio.get("action_count") or 0),
            "note": "组合动作备忘里沉淀出的可执行建议数量。",
            "tone": "neutral",
        },
        {
            "title": "执行前检查",
            "value": code_label(portfolio.get("execution_precheck_status")),
            "note": "这一层决定今天更适合直接推进，还是继续观察。",
            "tone": status_tone(portfolio.get("execution_precheck_status")),
        },
    ]

    body = (
        "<section class='panel'>"
        "<h2>结论先看</h2>"
        "<div class='section-intro'>这里先给投资判断、组合口径和机会状态；数据新鲜度、自动链运行记录放到自动运营页。</div>"
        f"<p>{escape(compact_text(report_summary, 220))}</p>"
        f"{render_metric_grid(conclusion_metrics)}"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>今日动作口径</h2>"
        "<div class='section-intro'>先看今天应该推进、暂缓还是继续观察。</div>"
        f"<ul>{primary_calls}</ul>"
        f"<div class='source-link'>{link_for_artifact(portfolio.get('artifact'))}</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>置顶机会与风险</h2>"
        "<div class='section-intro'>只列当前最需要人工判断的机会，不展示系统运行状态。</div>"
        f"{render_html_table(['标的', '分数', '状态', '主要风险', '下一步'], top_opportunity_rows, '当前没有置顶机会。')}"
        "</article>"
        "</section>"
        "<section class='report-layout'>"
        "<div class='panel-stack'>"
        "<article class='panel'>"
        "<h2>日报阅读入口</h2>"
        f"<div class='section-intro'>{escape(report_mode_note)}</div>"
        f"<ul>{risk_points_html}</ul>"
        "<div class='source-link'>"
        f"{link_for_artifact(active_report_artifact)}"
        "</div>"
        "</article>"
        f"{render_capital_flow_fact_panel(capital)}"
        "<article class='panel'>"
        "<h2>价格区间推演摘要</h2>"
        "<div class='section-intro'>这层补的是短周期节奏判断，帮助你把日报结论和下一交易日/5日运行区间直接对上。</div>"
        f"<ul>{forecast_overview_html}</ul>"
        f"{render_html_table(['对象', '方向', '下一交易日区间', '5日区间', '主要驱动'], forecast_focus_rows, '当前还没有重点推演对象。')}"
        f"<div class='story-footer' style='margin-top:12px'><a href='/analysis'>去个股分析页看完整推演</a> · {link_for_artifact(analysis_forecast.get('artifact'))}</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>关联动作文件</h2>"
        "<div class='section-intro'>如果要继续往组合动作和执行层看，从这里往下钻。</div>"
        f"<ul class='summary-list'><li>{link_for_artifact(portfolio.get('artifact'))}</li></ul>"
        "</article>"
        "<article class='panel'>"
        "<h2>跨市场资金异动总览</h2>"
        "<div class='section-intro'>这一块专门看当前系统覆盖库里的 A股、港股、美股异动榜和最新资讯，不再只盯持仓票。</div>"
        f"<div class='muted'>覆盖范围：A股 {escape(fmt_number(market_flow_coverage.get('a_share_count') or 0))} 只 / 港股 {escape(fmt_number(market_flow_coverage.get('hk_count') or 0))} 只 / 美股 {escape(fmt_number(market_flow_coverage.get('us_count') or 0))} 只。</div>"
        f"<div class='muted' style='margin-top:8px'>{escape(business_text(market_flow_coverage.get('scope_note') or '当前只按已覆盖库扫描。'))}</div>"
        f"<ul style='margin-top:12px'>{market_flow_overview_html}</ul>"
        f"<div class='source-link'>{link_for_artifact(market_flow.get('artifact'))}</div>"
        "</article>"
        f"{render_market_flow_anomaly_table('A股资金异动', market_flow_a_items, state, '当前没有 A股异动榜单。')}"
        f"{render_market_flow_anomaly_table('港股资金异动', market_flow_h_items, state, '当前没有港股异动榜单。')}"
        f"{render_market_flow_anomaly_table('美股资金异动', market_flow_us_items, state, '当前没有美股异动榜单。')}"
        f"{render_official_material_panel(official_material_items, '官方一手材料', '这一块只放今天值得优先看的官方材料，比如电话会稿、业绩稿、演示稿和投资者关系活动记录。', '当前没有新的官方一手材料摘要。', detail_enabled_codes)}"
        f"{render_public_transcript_panel(public_transcript_items, '公开电话会文字稿', '这一块专门放公开可得的电话会文字稿，用来复核管理层原话和会中表述变化。', '当前没有新的公开电话会文字稿摘要。', detail_enabled_codes)}"
        f"{render_external_research_panel(external_research_items, '外部研究锚点', '这一块保留还能参考的研究锚点，帮助判断当前市场在用什么研究口径。', '当前没有新的外部研究锚点。', detail_enabled_codes)}"
        f"{render_public_signal_panel(public_signal_items, '公开卖方参照', '这一块只放今天可直接参考的公开卖方一致预期，帮助快速判断市场预期是不是已经走得太满。', '当前没有新的公开卖方参照。', detail_enabled_codes)}"
        "</div>"
        "<article class='panel'>"
        "<h2>日报正文</h2>"
        f"<div class='section-intro'>{escape(report_mode_note)} 这里展示完整阅读版内容，不再直接贴原始 Markdown。</div>"
        f"{render_markdown_block(report_body)}"
        "</article>"
        "</section>"
    )
    return render_shell(
        page_title="SMR 日报",
        current_path="/reports",
        hero_title=report_title,
        hero_subtitle="先看结论、动作口径、机会和风险；系统状态细节已收进自动运营页。",
        body=body,
        refresh_seconds=refresh_seconds,
        show_status_strip=False,
        hero_facts=[
            ("组合口径", risk_decision.get("portfolio_state_label") or code_label(risk_decision.get("portfolio_state")) or "-"),
            ("证据缺口", evidence_gap_count),
            ("纸面观察", paper_watch_count),
            ("动作建议", portfolio.get("action_count") or 0),
            ("买入候选", risk_decision.get("buy_candidate_count") or 0),
            ("卖出候选", risk_decision.get("sell_candidate_count") or 0),
        ],
        **shell_state_kwargs(state),
    )


def render_analysis_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    analysis_forecast = state.get("analysis_forecast") or {}
    coverage = analysis_forecast.get("coverage_summary") or {}
    focus_items = sorted(
        analysis_forecast.get("all_equities") or [],
        key=lambda item: (
            -(abs((item.get("next_day") or {}).get("bias_pct") or 0)),
            -((item.get("confidence") or 0)),
        ),
    )[:6]
    overview_html = "".join(
        f"<li>{escape(business_text(item))}</li>" for item in (analysis_forecast.get("overview_lines") or [])
    ) or "<li>当前还没有提取到完整的推演结论。</li>"
    metrics = [
        {
            "title": "最近快照",
            "value": analysis_forecast.get("created_at") or "-",
            "note": "这页直接使用最近一轮区间推演快照。",
            "tone": status_tone(analysis_forecast.get("status")),
        },
        {
            "title": "可推演个股",
            "value": fmt_number(analysis_forecast.get("equity_count") or 0),
            "note": "按当前活跃覆盖池和已有行情窗口生成。",
            "tone": "good" if (analysis_forecast.get("equity_count") or 0) > 0 else "warning",
        },
        {
            "title": "A股覆盖",
            "value": fmt_number(coverage.get("a_share_count") or 0),
            "note": f"最近随时行情日 {coverage.get('a_share_trade_date') or '-'}。",
            "tone": "neutral",
        },
        {
            "title": "港股覆盖",
            "value": fmt_number(coverage.get("hk_count") or 0),
            "note": f"最近随时行情日 {coverage.get('hk_trade_date') or '-'}。",
            "tone": "neutral",
        },
        {
            "title": "美股覆盖",
            "value": fmt_number(coverage.get("us_count") or 0),
            "note": f"最近随时行情日 {coverage.get('us_trade_date') or '-'}。",
            "tone": "neutral",
        },
        {
            "title": "指数代理",
            "value": fmt_number(analysis_forecast.get("index_proxy_count") or 0),
            "note": "这里只做覆盖篮子方向代理，不做真实指数拟合承诺。",
            "tone": "good" if (analysis_forecast.get("index_proxy_count") or 0) > 0 else "warning",
        },
    ]
    body = (
        f"{render_market_fact_panel(overview, capital, '分析页事实口径')}"
        "<section class='panel'>"
        "<h2>本轮推演总览</h2>"
        "<div class='section-intro'>这一页专门回答短周期里哪些票更像偏多推进、哪些更像先别追，以及 A股 / 港股 / 美股在当前覆盖样本里的整体方向代理。</div>"
        f"{render_metric_grid(metrics)}"
        f"<div style='margin-top:16px'><ul>{overview_html}</ul></div>"
        f"<div class='muted' style='margin-top:10px'>方法：{escape(business_text(analysis_forecast.get('methodology') or '-'))}</div>"
        f"<div class='muted' style='margin-top:8px'>说明：{escape(business_text(analysis_forecast.get('note') or '-'))}</div>"
        f"<div class='source-link' style='margin-top:12px'>{link_for_artifact(analysis_forecast.get('artifact'))}</div>"
        "</section>"
        f"{render_index_proxy_cards(analysis_forecast.get('index_proxies') or [])}"
        f"{render_forecast_focus_cards(focus_items, state, '当前还没有可用的重点推演对象。')}"
        f"{render_analysis_forecast_table('A股个股区间推演', (analysis_forecast.get('equities_by_market') or {}).get('A') or [], state, '当前没有 A股区间推演结果。')}"
        f"{render_analysis_forecast_table('港股个股区间推演', (analysis_forecast.get('equities_by_market') or {}).get('H') or [], state, '当前没有港股区间推演结果。')}"
        f"{render_analysis_forecast_table('美股个股区间推演', (analysis_forecast.get('equities_by_market') or {}).get('US') or [], state, '当前没有美股区间推演结果。')}"
    )
    return render_shell(
        page_title="SMR 个股分析",
        current_path="/analysis",
        hero_title="个股分析",
        hero_subtitle="把当前覆盖股票的短周期区间推演单独拆出来，先看方向和区间，再决定是否继续深挖研究或推进动作。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("最近快照", analysis_forecast.get("created_at") or "-"),
            ("可推演个股", analysis_forecast.get("equity_count") or 0),
            ("A股", coverage.get("a_share_count") or 0),
            ("港股", coverage.get("hk_count") or 0),
            ("美股", coverage.get("us_count") or 0),
            ("指数代理", analysis_forecast.get("index_proxy_count") or 0),
        ],
        **shell_state_kwargs(state),
    )


def render_opportunities_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    opportunity_engine = state.get("opportunity_engine") or {}
    radar = opportunity_engine.get("radar") or {}
    evidence = opportunity_engine.get("evidence") or {}
    attack_defense = opportunity_engine.get("attack_defense") or {}
    lifecycle = opportunity_engine.get("lifecycle") or {}
    paper_watchlist = opportunity_engine.get("paper_watchlist") or {}
    paper_performance = opportunity_engine.get("paper_performance") or {}
    deep_analysis = state.get("deep_analysis") or {}
    overview_lines = "".join(
        f"<li>{escape(business_text(line))}</li>" for line in (deep_analysis.get("overview_lines") or [])
    ) or "<li>当前还没有形成可读结论。</li>"
    coverage_gap_rows = []
    for item in (deep_analysis.get("coverage_gaps") or [])[:8]:
        coverage_gap_rows.append(
            [
                escape(item.get("name") or "-"),
                escape(item.get("ts_code") or "-"),
                escape(" / ".join(code_label(theme) for theme in (item.get("themes") or [])) or "-"),
                escape(code_label(item.get("reason") or "-")),
            ]
        )

    metrics = [
        {
            "title": "最近快照",
            "value": deep_analysis.get("created_at") or "-",
            "note": "当前页面直接消费最近一轮深度分析快照。",
            "tone": status_tone(deep_analysis.get("status")),
        },
        {
            "title": "更新频率",
            "value": f"{deep_analysis.get('cadence_hours') or 12} 小时",
            "note": "按主题机会扫描节奏刷新。",
            "tone": "good",
        },
        {
            "title": "主题数量",
            "value": fmt_number(deep_analysis.get("theme_count") or 0),
            "note": "当前重点覆盖 AI、光通信、新能源、scale up、scale out。",
            "tone": "neutral",
        },
        {
            "title": "A股候选",
            "value": fmt_number(deep_analysis.get("a_share_candidate_count") or 0),
            "note": "当前有明确继续深挖价值的 A 股标的数。",
            "tone": "good" if (deep_analysis.get("a_share_candidate_count") or 0) > 0 else "ghost",
        },
        {
            "title": "美股候选",
            "value": fmt_number(deep_analysis.get("us_candidate_count") or 0),
            "note": "当前有明确继续深挖价值的美股标的数。",
            "tone": "good" if (deep_analysis.get("us_candidate_count") or 0) > 0 else "ghost",
        },
        {
            "title": "覆盖缺口",
            "value": fmt_number(len(deep_analysis.get("coverage_gaps") or [])),
            "note": "缺的是价格或已有数据覆盖，不是系统内部状态。",
            "tone": "warning" if (deep_analysis.get("coverage_gaps") or []) else "good",
        },
    ]
    radar_items = flatten_radar_market_items(radar, limit=12)
    radar_overview_html = "".join(
        f"<li>{escape(business_text(line))}</li>" for line in (radar.get("overview_lines") or [])
    ) or "<li>当前还没有主动雷达快照。</li>"
    active_metrics = [
        {
            "title": "主动雷达",
            "value": radar.get("created_at") or "-",
            "note": f"覆盖打分 {fmt_number(radar.get('scored_count') or 0)} 个，候选 {fmt_number(radar.get('candidate_count') or 0)} 个。",
            "tone": status_tone(radar.get("status")),
            "footer_html": link_for_artifact(radar.get("artifact")),
        },
        {
            "title": "纸面候选",
            "value": fmt_number(radar.get("paper_watch_candidate_count") or 0),
            "note": "雷达层达到纸面观察阈值的候选数。",
            "tone": "good" if (radar.get("paper_watch_candidate_count") or 0) > 0 else "ghost",
        },
        {
            "title": "策略证据",
            "value": fmt_number(evidence.get("ready_count") or 0),
            "note": f"已验证 {fmt_number(evidence.get('candidate_count') or 0)} 个雷达候选。",
            "tone": "good" if (evidence.get("ready_count") or 0) > 0 else status_tone(evidence.get("status")),
            "footer_html": link_for_artifact(evidence.get("artifact")),
        },
        {
            "title": "攻防推演",
            "value": fmt_number(attack_defense.get("case_count") or 0),
            "note": f"纸面就绪 {fmt_number(attack_defense.get('paper_watch_ready_count') or 0)} 个 / 先补研究 {fmt_number(attack_defense.get('research_first_count') or 0)} 个。",
            "tone": status_tone(attack_defense.get("status")),
            "footer_html": link_for_artifact(attack_defense.get("artifact")),
        },
        {
            "title": "纸面观察单",
            "value": fmt_number(paper_watchlist.get("ticket_count") or 0),
            "note": "paper_only；不包含真实下单或券商指令。",
            "tone": "good" if (paper_watchlist.get("ticket_count") or 0) > 0 else status_tone(paper_watchlist.get("status")),
            "footer_html": link_for_artifact(paper_watchlist.get("artifact")),
        },
        {
            "title": "生命周期",
            "value": fmt_number((lifecycle.get("state_counts") or {}).get("new_candidate") or 0),
            "note": f"新进 / 强化 / 降温：{fmt_number((lifecycle.get('state_counts') or {}).get('new_candidate') or 0)} / {fmt_number(((lifecycle.get('state_counts') or {}).get('promoted') or 0) + ((lifecycle.get('state_counts') or {}).get('strengthening') or 0))} / {fmt_number(((lifecycle.get('state_counts') or {}).get('cooling') or 0) + ((lifecycle.get('state_counts') or {}).get('demoted') or 0))}。",
            "tone": status_tone(lifecycle.get("status")),
            "footer_html": link_for_artifact(lifecycle.get("artifact")),
        },
        {
            "title": "纸面复盘",
            "value": fmt_number(paper_performance.get("evaluated_ticket_count") or 0),
            "note": f"触发 {fmt_number((paper_performance.get('status_counts') or {}).get('trigger_confirmed') or 0)} / 失效 {fmt_number((paper_performance.get('status_counts') or {}).get('invalidated') or 0)}。",
            "tone": status_tone(paper_performance.get("status")),
            "footer_html": link_for_artifact(paper_performance.get("artifact")),
        },
    ]

    body = (
        f"{render_market_fact_panel(overview, capital, '市场事实口径')}"
        "<section class='panel'>"
        "<h2>主动机会雷达</h2>"
        "<div class='section-intro'>这一块借鉴 QuantDinger 的闭环、Qlib 的因子排序、vectorbt 的证据先行和 vn.py 的事件驱动思路：先发现，再验证，再攻防，最后只进入纸面观察。</div>"
        f"{render_metric_grid(active_metrics)}"
        f"<div style='margin-top:18px'><ul>{radar_overview_html}</ul></div>"
        "</section>"
        "<section class='panel'>"
        "<h2>雷达候选</h2>"
        "<div class='section-intro'>这些是系统主动从当前覆盖库里挑出来的候选，不等同于推荐买入。</div>"
        f"{render_active_radar_cards(radar_items, state, '当前还没有主动雷达候选。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>策略证据</h2>"
        "<div class='section-intro'>轻量历史验证先回答“这个信号过去有没有基本可复核的胜率和收益特征”。</div>"
        f"{render_strategy_evidence_table(evidence.get('items') or [])}"
        "</section>"
        "<section class='panel'>"
        "<h2>攻防推演</h2>"
        "<div class='section-intro'>每个机会都必须同时给出支持项、攻击点和失效条件，避免只看多头故事。</div>"
        f"{render_attack_defense_table(attack_defense.get('cases') or [])}"
        "</section>"
        "<section class='panel'>"
        "<h2>机会生命周期</h2>"
        "<div class='section-intro'>这里回答“今天的机会是新冒出来、继续强化、开始降温，还是已经退出雷达”。</div>"
        f"{render_lifecycle_table(lifecycle.get('items') or [])}"
        "</section>"
        "<section class='panel'>"
        "<h2>纸面观察单</h2>"
        "<div class='section-intro'>这里只做 paper-only 观察，不产生真实交易指令。真实组合动作仍走现有组合和风控门禁。</div>"
        f"{render_paper_ticket_table(paper_watchlist.get('tickets') or [])}"
        "</section>"
        "<section class='panel'>"
        "<h2>纸面表现复盘</h2>"
        "<div class='section-intro'>纸面单不是写完就算结束；这层负责记录后续行情是否触发、失效或仍待验证。</div>"
        f"{render_paper_performance_table(paper_performance.get('items') or [])}"
        "</section>"
        "<section class='panel'>"
        "<h2>本轮结论</h2>"
        "<div class='section-intro'>这一页只回答两个问题：哪些主题还值得继续挖，哪些 A 股 / 美股票当前更像被低估而不是单纯热门。</div>"
        f"{render_metric_grid(metrics)}"
        f"<div style='margin-top:18px'><ul>{overview_lines}</ul></div>"
        f"<div class='source-link'>{link_for_artifact(deep_analysis.get('artifact'))}</div>"
        "</section>"
        "<section class='panel'>"
        "<h2>主题雷达</h2>"
        "<div class='section-intro'>先看方向，再看个股。主题强度代表当前继续放资源去深挖的性价比。</div>"
        f"{render_theme_radar_cards(deep_analysis.get('theme_radar') or [])}"
        "</section>"
        f"{render_opportunity_cards('A股低估候选', deep_analysis.get('a_share_candidates') or [], state, '当前还没有形成可读的 A 股低估候选。')}"
        f"{render_opportunity_cards('美股低估候选', deep_analysis.get('us_candidates') or [], state, '当前还没有形成可读的美股低估候选。')}"
    )
    if coverage_gap_rows:
        body += (
            "<section class='panel'>"
            "<h2>待补覆盖</h2>"
            "<div class='section-intro'>这一块不是系统状态，而是业务覆盖仍然不足的标的，后续要决定是否继续补数和补源。</div>"
            f"{render_html_table(['名称', '代码', '主题', '缺口'], coverage_gap_rows, '当前没有覆盖缺口。')}"
            "</section>"
        )
    return render_shell(
        page_title="SMR 机会挖掘",
        current_path="/opportunities",
        hero_title="机会挖掘",
        hero_subtitle="基于主题聚合后的深度分析结果，重点输出 AI、光通信、新能源、scale up、scale out 方向的被低估 A 股和美股。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("主动雷达", radar.get("created_at") or "-"),
            ("纸面观察单", paper_watchlist.get("ticket_count") or 0),
            ("最近快照", deep_analysis.get("created_at") or "-"),
            ("主题数量", deep_analysis.get("theme_count") or 0),
            ("A股候选", deep_analysis.get("a_share_candidate_count") or 0),
            ("美股候选", deep_analysis.get("us_candidate_count") or 0),
            ("两融事实日", capital.get("margin_balance", {}).get("anchor_trade_date") or "-"),
            ("互联互通日频", capital.get("stock_connect", {}).get("anchor_trade_date") or "-"),
        ],
        **shell_state_kwargs(state),
    )


def render_research_detail_page(state: dict, ts_code: str, refresh_seconds: int) -> tuple[int, str]:
    item = find_watch_item(state, ts_code)
    if not item:
        body = render_shell(
            page_title="研究详情",
            current_path="/research",
            hero_title="研究详情不存在",
            hero_subtitle="当前没有找到对应标的的研究详情。",
            body="<section class='panel'><div class='empty'>请从研究观察或调仓动作页面重新进入。</div></section>",
            refresh_seconds=refresh_seconds,
            **shell_state_kwargs(state),
        )
        return 404, body

    detail_context = detail_context_for_symbol(state, ts_code)
    related_actions = []
    for action in state.get("portfolio_action", {}).get("actions") or []:
        legs = [((action.get("add") or {}).get("ts_code")), ((action.get("remove") or {}).get("ts_code")), ((action.get("subject") or {}).get("ts_code"))]
        if ts_code in legs:
            related_actions.append(action)

    official_material = detail_context.get("official_material") or {}
    external_research = detail_context.get("external_research") or {}
    public_transcript = detail_context.get("public_transcript") or {}
    forecast = detail_context.get("forecast") or {}
    upcoming_events = detail_context.get("upcoming_events") or item.get("upcoming_event_calendar") or []
    official_source_paths = official_material_source_rel_paths(official_material or item)
    external_source_rel_path = (external_research or {}).get("source_rel_path") or item.get("source_rel_path")
    public_transcript_source_rel_path = public_transcript.get("source_rel_path")

    evidence_rows = [
        [
            "价格与节奏",
            f"最新收盘 {fmt_number(item.get('latest_close'))} / 日涨跌 {fmt_pct(item.get('latest_pct_chg'))} / 交易日 {item.get('latest_trade_date') or '-'}",
        ],
        [
            "均线与强度",
            f"MA20 {fmt_number(item.get('ma_20'))} / MA60 {fmt_number(item.get('ma_60'))} / MA120 {fmt_number(item.get('ma_120'))} / 趋势强度 {fmt_number(item.get('trend_strength'))} / RSI14 {fmt_number(item.get('rsi_14'))}",
        ],
        [
            "估值与增长",
            f"PE(TTM) {fmt_number(item.get('pe_ttm'))} / PB {fmt_number(item.get('pb'))} / 营收同比 {fmt_pct(item.get('revenue_yoy'))} / 净利润同比 {fmt_pct(item.get('net_profit_yoy'))}",
        ],
        [
            "官方一手材料",
            official_material_summary(official_material or item),
        ],
        [
            "电话会文字稿",
            public_transcript_summary(public_transcript),
        ],
        [
            "外部研究锚点",
            external_research_summary(external_research or item),
        ],
        [
            "公开卖方参照",
            public_signal_summary(item),
        ],
        [
            "信号标签",
            ", ".join(code_label(tag) for tag in (item.get("signal_tags") or [])) or "-",
        ],
    ]
    evidence_html = render_html_table(
        ["维度", "当前证据"],
        [[escape(left), escape(right)] for left, right in evidence_rows],
        "当前没有证据数据。",
    )

    watchpoints = "".join(f"<li>{escape(business_text(point))}</li>" for point in (item.get("watchpoints") or []))
    next_checks = "".join(f"<li>{escape(business_text(point))}</li>" for point in (item.get("next_check_items") or []))
    related_action_items = []
    for action in related_actions:
        title_html = render_action_title_link(action)
        summary = business_text(action.get("summary") or "-")
        related_action_items.append(f"<li>{title_html}<div class='muted'>{escape(summary)}</div></li>")
    related_actions_html = f"<ul class='summary-list'>{''.join(related_action_items)}</ul>" if related_action_items else "<div class='empty'>当前没有直接关联的组合动作。</div>"

    sources = [
        item.get("card_rel_path"),
        public_transcript_source_rel_path,
        external_source_rel_path,
        item.get("public_analyst_source_rel_path"),
        *official_source_paths[:3],
    ]
    signal_badges = render_badge_group([(code_label(tag), "ghost") for tag in (item.get("signal_tags") or [])]) if item.get("signal_tags") else "<span class='muted'>暂无信号标签</span>"
    external_research_brief = " / ".join(
        part
        for part in [
            (external_research or {}).get("org_name") or item.get("external_research_org"),
            (external_research or {}).get("rating_name") or item.get("external_research_rating"),
            (external_research or {}).get("published_at") or item.get("external_research_published_at"),
        ]
        if part
    )
    external_research_html = (
        f"<div>{escape(external_research_summary(external_research or item))}</div><div class='muted' style='margin-top:8px'>{link_for_rel_path(external_source_rel_path, '查看外部研报') if external_source_rel_path else '暂无可点击外部研报'}</div>"
        if external_research_brief or external_source_rel_path
        else "<div class='empty'>当前没有可展示的外部研究锚点。</div>"
    )
    official_material_html = (
        f"<div>{escape(official_material_summary(official_material or item))}</div>"
        f"<div class='muted' style='margin-top:8px'>{escape(compact_text(official_material_latest_title(official_material or item), 88) if official_material_latest_title(official_material or item) else '暂无标题锚点')}</div>"
        f"<div class='muted' style='margin-top:8px'>{render_source_list(official_source_paths[:3], '暂无可点击官方原文。')}</div>"
        if official_material or official_source_paths
        else "<div class='empty'>当前没有可展示的官方一手材料。</div>"
    )
    public_signal_html = (
        f"<div>{escape(public_signal_summary(item))}</div>"
        f"<div class='muted' style='margin-top:8px'>{link_for_rel_path(item.get('public_analyst_source_rel_path'), '查看公开卖方原文') if item.get('public_analyst_source_rel_path') else '暂无可点击公开卖方原文'}</div>"
        if public_signal_label(item) or item.get("public_analyst_source_rel_path")
        else "<div class='empty'>当前没有可展示的公开卖方参照。</div>"
    )
    public_transcript_html = (
        f"<div>{escape(public_transcript_summary(public_transcript))}</div>"
        f"<div class='muted' style='margin-top:8px'>发言人：{escape(', '.join((public_transcript.get('speakers') or [])[:6]) if (public_transcript.get('speakers') or []) else '当前没有提取到发言人名单')}</div>"
        f"<div class='muted' style='margin-top:8px'>{link_for_rel_path(public_transcript_source_rel_path, '查看电话会文字稿') if public_transcript_source_rel_path else '暂无可点击电话会文字稿'}</div>"
        if public_transcript or public_transcript_source_rel_path
        else "<div class='empty'>当前没有可展示的公开电话会文字稿。</div>"
    )

    body = (
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>当前结论</h2>"
        f"<div class='section-intro'>{escape(business_text(item.get('trend_summary') or '-'))}</div>"
        f"<div class='muted'>主要矛盾：{escape(focus_tension_text(item))}</div>"
        "<div class='split' style='margin-top:14px'>"
        f"<div><h4>关键观察点</h4><ul>{watchpoints or '<li>-</li>'}</ul></div>"
        f"<div><h4>下一检查项</h4><ul>{next_checks or '<li>-</li>'}</ul></div>"
        "</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>证据锚点</h2>"
        "<div class='section-intro'>这里把价格、均线、估值、增长和外部研究锚点集中放在一起。</div>"
        f"{evidence_html}"
        "</article>"
        "</section>"
        "<section class='grid-3'>"
        f"{render_symbol_events_panel(upcoming_events, '未来催化')}"
        f"{render_symbol_events_panel(detail_context.get('recent_events') or [], '最近事件')}"
        f"{render_symbol_forecast_panel(forecast)}"
        f"{render_symbol_capital_flow_panel(detail_context)}"
        f"{render_symbol_risk_panel(detail_context)}"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>关联动作</h2>"
        "<div class='section-intro'>如果这个标的已经出现在组合动作里，这里直接给到对应动作入口。</div>"
        f"{related_actions_html}"
        "</article>"
        "<article class='panel'>"
        "<h2>参考材料</h2>"
        "<div class='section-intro'>如果你要核对底稿和外部研报，从这里进入；正文区不再直接堆原始字段。</div>"
        f"{render_source_list(sources, '当前没有可点击的研究原文。')}"
        "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>补充信号</h2>"
        "<div class='section-intro'>这里只保留真正有用的辅助信号，不再直接嵌底稿字段列表。</div>"
        f"{signal_badges}"
        "</article>"
        "<article class='panel'>"
        "<h2>官方一手材料</h2>"
        "<div class='section-intro'>优先看公告、电话会稿、演示稿和投资者关系活动记录，这层最接近管理层原话。</div>"
        f"{official_material_html}"
        "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>公开电话会文字稿</h2>"
        "<div class='section-intro'>这层专门用来复核管理层在电话会里的原话、节奏和重点表述变化。</div>"
        f"{public_transcript_html}"
        "</article>"
        "<article class='panel'>"
        "<h2>公开卖方参照</h2>"
        "<div class='section-intro'>这层不是全文研报，而是公开一致预期和目标价空间，用来看市场预期站在哪。</div>"
        f"{public_signal_html}"
        "</article>"
        "<article class='panel'>"
        "<h2>外部研究锚点</h2>"
        "<div class='section-intro'>保留研究机构、评级和时间，方便你判断这个研究锚点还值不值得信。</div>"
        f"{external_research_html}"
        "</article>"
        "</section>"
    )
    return (
        200,
        render_shell(
            page_title=f"SMR 研究详情 - {item.get('name') or ts_code}",
            current_path="/research",
            hero_title=f"{item.get('name') or '-'} / {ts_code}",
            hero_subtitle="单票研究详情页。先看当前结论、主要矛盾和证据锚点，再决定是否继续看原文。",
            body=body,
            refresh_seconds=refresh_seconds,
            hero_facts=[
                ("当前口径", code_label(item.get("objective_view"))),
                ("优先级", code_label(item.get("priority"))),
                ("所在池", code_label(item.get("primary_pool"))),
                ("最新日涨跌", fmt_pct(item.get("latest_pct_chg"))),
                ("短周期方向", code_label(forecast.get("bias_label"))),
                ("官方材料", code_label(official_material_freshness(official_material or item))),
                ("电话会稿", code_label(public_transcript.get("freshness_label"))),
                ("卖方参照", code_label(public_signal_label(item))),
                ("未来催化", len(upcoming_events)),
                ("最近事件", len(detail_context.get("recent_events") or [])),
            ],
            **shell_state_kwargs(state),
        ),
    )


def render_action_detail_page(state: dict, action_id: str, refresh_seconds: int) -> tuple[int, str]:
    action = find_action(state, action_id)
    if not action:
        body = render_shell(
            page_title="动作详情",
            current_path="/portfolio",
            hero_title="动作详情不存在",
            hero_subtitle="当前没有找到对应动作的详情。",
            body="<section class='panel'><div class='empty'>请从调仓动作页面重新进入。</div></section>",
            refresh_seconds=refresh_seconds,
            **shell_state_kwargs(state),
        )
        return 404, body

    add_leg = action.get("add") or {}
    remove_leg = action.get("remove") or {}
    subject = action.get("subject") or {}
    add_item = find_watch_item(state, add_leg.get("ts_code")) if add_leg else None
    remove_item = find_watch_item(state, remove_leg.get("ts_code")) if remove_leg else None
    subject_item = find_watch_item(state, subject.get("ts_code")) if subject else None
    report_sections = render_report_driven_action_sections(state, action)
    amount_label = fmt_money_cn(action.get("trade_amount"))
    if amount_label == "-":
        amount_label = "见操作计划"
    hero_facts = [
        ("候选动作", action.get("title") or action_id),
        ("金额口径", amount_label),
        ("执行口径", "人工复核后分批推进"),
        ("复核重点", "调出理由、订单/毛利率、竞争格局"),
    ]

    if report_sections:
        body = f"{render_action_deep_report_panel(state, action)}{report_sections}"
    else:
        body = (
            f"{render_action_deep_report_panel(state, action)}"
            f"{render_action_operation_report(state, action, add_item, remove_item, subject_item)}"
            f"{render_action_logic_report(state, action, add_item, remove_item, subject_item)}"
            f"{render_action_technical_report(state, action, add_item, remove_item, subject_item)}"
        )
    return (
        200,
        render_shell(
            page_title=f"SMR 动作详情 - {action.get('title') or action_id}",
            current_path="/portfolio",
            hero_title=action.get("title") or "动作详情",
            hero_subtitle="这页只保留三件事：怎么操作、为什么这么调、技术证据是否支持。",
            body=body,
            refresh_seconds=refresh_seconds,
            hero_facts=hero_facts,
            show_status_strip=False,
            **shell_state_kwargs(state),
        ),
    )


def render_research_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    strategy = state["strategy_watch"]
    reporting = state["reporting"]
    detail_enabled_codes = {item.get("ts_code") for item in iter_unique_watch_items(state) if item.get("ts_code")}
    items = strategy.get("top_focus_items") or []
    high_items = [item for item in items if item.get("priority") == "high"]
    mainline_items = [item for item in items if item.get("objective_view") in {"trend_follow", "trend_positive"}]
    repair_items = [item for item in items if item.get("objective_view") not in {"trend_follow", "trend_positive"}]
    official_material_items = ((reporting.get("official_material_digest") or {}).get("items") or [])[:5]
    public_transcript_items = ((reporting.get("public_transcript_digest") or {}).get("items") or [])[:5]
    external_research_items = ((reporting.get("external_research_digest") or {}).get("items") or [])[:5]
    source_paths = [((strategy.get("artifact") or {}).get("rel_path"))]
    for item in items:
        source_paths.extend(
            [
                item.get("card_rel_path"),
                public_transcript_source_rel_path(item),
                item.get("public_analyst_source_rel_path"),
                item.get("source_rel_path"),
                *((item.get("official_material_source_rel_paths") or [])[:1]),
            ]
        )
    source_paths.extend(item.get("source_rel_path") for item in public_transcript_items)

    body = (
        f"{render_market_fact_panel(overview, capital, '研究页事实口径')}"
        f"{render_focus_overview_table('研究总览', items, '先看一遍当前研究对象、为什么看、主要矛盾和下一步，不需要先钻原文。', '当前没有研究对象。')}"
        "<section class='panel'>"
        "<h2>主线跟踪</h2>"
        "<div class='section-intro'>这里放趋势仍在、值得继续顺着看的对象，重点是主线是否延续以及兑现能否跟上。</div>"
        f"{render_focus_cards(mainline_items, '当前没有主线跟踪对象。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>问题复核</h2>"
        "<div class='section-intro'>这里放需要修复、确认或重新验证的对象，重点不是追，而是看问题是否在收敛。</div>"
        f"{render_focus_cards(repair_items, '当前没有需要单独复核的对象。')}"
        "</section>"
        f"{render_official_material_panel(official_material_items, '官方一手跟踪', '这里集中看今天真正值得往下钻的电话会稿、业绩稿、演示稿和投资者关系活动记录。', '当前没有新的官方一手跟踪对象。', detail_enabled_codes)}"
        f"{render_public_transcript_panel(public_transcript_items, '电话会文字跟踪', '这里集中看公开电话会文字稿，重点复核管理层原话和会中信息密度。', '当前没有新的电话会文字跟踪对象。', detail_enabled_codes)}"
        f"{render_external_research_panel(external_research_items, '研究锚点跟踪', '这里集中看还能参考的研究锚点，避免研究页只剩价格和情绪。', '当前没有新的研究锚点。', detail_enabled_codes)}"
        "<section class='panel'>"
        "<h2>研究材料</h2>"
        "<div class='section-intro'>如果要继续看批次原文和单票研究，从这里往下钻，不再把原始批次直接堆在页面底部。</div>"
        f"{render_source_list(source_paths, '当前没有研究原文入口。')}"
        "</section>"
    )
    return render_shell(
        page_title="SMR 研究观察",
        current_path="/research",
        hero_title="研究观察",
        hero_subtitle="这一页只看标的研究和盯盘对象，核心是当前为什么盯、下一步怎么盯。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("观察对象", strategy.get("item_count") or 0),
            ("聚焦范围", strategy.get("focus_strategy") or "-"),
            ("高优先级", len(high_items)),
            ("主线跟踪", len(mainline_items)),
            ("电话会稿", len(public_transcript_items)),
            ("两融事实日", capital.get("margin_balance", {}).get("anchor_trade_date") or "-"),
            ("互联互通日频", capital.get("stock_connect", {}).get("anchor_trade_date") or "-"),
        ],
        **shell_state_kwargs(state),
    )


def render_portfolio_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    portfolio = state["portfolio_action"]
    rotation = state["rotation"]
    all_actions = portfolio.get("actions") or []
    primary_calls = "".join(f"<li>{escape(business_text(item))}</li>" for item in (portfolio.get("primary_call") or []))
    if not primary_calls:
        primary_calls = "<li>当前没有组合动作主张。</li>"

    ready_actions = [item for item in all_actions if item.get("action_type") == "swap_ready"]
    watch_actions = [item for item in all_actions if item.get("action_type") == "swap_watch"]
    holding_actions = [item for item in all_actions if item.get("action_type") == "holding_watch"]
    action_rows = []
    for action in all_actions:
        action_rows.append(
            [
                (
                    f"{render_action_title_link(action)}"
                    f"<div class='muted'>{escape(business_text(action.get('summary') or '-'))}</div>"
                ),
                render_badge_group(
                    [
                        (action.get("priority"), "neutral"),
                        (action.get("action_type"), "ghost"),
                        (action.get("gate_status"), "ghost"),
                    ]
                ),
                escape(business_text((action.get("rationale") or [None])[0] or "-")),
                escape(business_text((action.get("next_checks") or [None])[0] or "-")),
            ]
        )
    key_docs = [
        (portfolio.get("artifact") or {}).get("rel_path"),
        (rotation.get("artifact") or {}).get("rel_path"),
        (rotation.get("execution_plan_artifact") or {}).get("rel_path"),
    ]
    for action in all_actions:
        key_docs.extend(action.get("source_refs") or [])

    body = (
        f"{render_market_fact_panel(overview, capital, '调仓页事实口径')}"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>组合动作主张</h2>"
        "<div class='section-intro'>这一页专门看调仓和组合动作，不再混研究和事件。</div>"
        f"<ul>{primary_calls}</ul>"
        "</article>"
        "<article class='panel'>"
        "<h2>支撑材料</h2>"
        "<div class='section-intro'>如果要继续核对轮动快照、执行方案和相关研究材料，从这里往下钻。</div>"
        f"{render_source_list(key_docs, '当前没有相关文件入口。')}"
        "</article>"
        "</section>"
        "<section class='panel'>"
        "<h2>动作总览</h2>"
        "<div class='section-intro'>先看所有动作当前处在哪个阶段、为什么会给出这条建议，再决定要不要细看下面的动作卡。</div>"
        f"{render_html_table(['动作', '当前阶段', '核心依据', '下一步'], action_rows, '当前没有动作建议。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>优先换仓</h2>"
        f"{render_action_cards(ready_actions, state, '当前没有可直接推进的换仓建议。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>观察换仓</h2>"
        f"{render_action_cards(watch_actions, state, '当前没有观察换仓建议。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>持仓复核</h2>"
        f"{render_action_cards(holding_actions, state, '当前没有需要复核的持仓对象。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>优先轮动对</h2>"
        f"{render_rotation_pairs(rotation.get('rotation_pairs') or [], '当前没有轮动对。')}"
        "</section>"
        "<section class='grid-2'>"
        f"{render_watch_table('优先调入候选', rotation.get('top_add_candidates') or [], '这部分只展示潜在调入腿，方便看为什么它们值得进组合。')}"
        f"{render_watch_table('优先调出参照', rotation.get('top_reduce_candidates') or [], '这部分只展示潜在调出腿，方便看现有弱项到底弱在哪。')}"
        "</section>"
    )
    return render_shell(
        page_title="SMR 调仓动作",
        current_path="/portfolio",
        hero_title="调仓动作",
        hero_subtitle="把调入、调出、轮动对和组合动作建议集中到一个页面，不和别的业务线混看。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("动作建议", portfolio.get("action_count") or 0),
            ("优先换仓", len(ready_actions)),
            ("轮动对", rotation.get("rotation_pair_count") or 0),
            ("两融事实日", capital.get("margin_balance", {}).get("anchor_trade_date") or "-"),
            ("互联互通日频", capital.get("stock_connect", {}).get("anchor_trade_date") or "-"),
        ],
        **shell_state_kwargs(state),
    )


def render_risk_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    risk = state["risk"]
    decision = risk.get("decision") or {}
    alerts = risk.get("recent_alerts") or []
    state_tone = {"normal": "good", "cautious": "warning", "blocked": "warning"}.get(
        decision.get("portfolio_state"), "ghost"
    )

    headline_items = "".join(
        f"<li>{escape(business_text(item))}</li>" for item in (decision.get("headline_actions") or [])
    ) or "<li>当前没有额外头条动作。</li>"
    constraint_items = "".join(
        f"<li>{escape(business_text(item))}</li>" for item in (decision.get("portfolio_constraints") or [])
    ) or "<li>当前没有额外组合约束。</li>"

    decision_summary = (
        "<section class='panel'>"
        "<h2>买卖决策总览</h2>"
        "<div class='section-intro'>先看组合层结论，再决定今天是该进攻、该减仓，还是只观察。</div>"
        "<div class='story-grid'>"
        "<article class='card'>"
        "<div class='card-header'>"
        "<div><h3>组合状态</h3><div class='muted'>先看这一层，再谈单票买卖。</div></div>"
        f"<div>{badge(decision.get('portfolio_state_label') or decision.get('portfolio_state') or '-', state_tone)}</div>"
        "</div>"
        f"<p>{escape(business_text(decision.get('portfolio_buy_call') or '当前没有买入侧结论。'))}</p>"
        f"<p>{escape(business_text(decision.get('portfolio_sell_call') or '当前没有卖出侧结论。'))}</p>"
        f"<div class='muted'>{link_for_artifact(decision.get('artifact'))}</div>"
        "</article>"
        "<article class='card'>"
        "<div class='card-header'>"
        "<div><h3>今日优先动作</h3><div class='muted'>把最该先处理的动作收口成一句人话。</div></div>"
        "</div>"
        f"<ul>{headline_items}</ul>"
        "</article>"
        "</div>"
        "<article class='card' style='margin-top:16px'>"
        "<h3>组合闸门</h3>"
        f"<ul>{constraint_items}</ul>"
        "</article>"
        "</section>"
    )

    def render_trade_card(item: dict, side: str) -> str:
        verdict = item.get("verdict")
        tone = {
            "buy": "good",
            "buy_small": "warning",
            "watch": "ghost",
            "block": "warning",
            "sell": "warning",
            "trim": "warning",
            "hold": "ghost",
        }.get(verdict, "ghost")
        linked = item.get("linked_remove") if side == "buy" else item.get("linked_buy")
        linked_text = "-"
        if isinstance(linked, dict):
            linked_text = linked.get("name") or linked.get("ts_code") or "-"
        tranche_pct = item.get("suggested_tranche_pct")
        meta_rows = [f"score={item.get('score') or '-'}"]
        if side == "buy":
            meta_rows.append(f"建议仓位={f'{tranche_pct * 100:.2f}%' if tranche_pct not in (None, '') else '-'}")
            meta_rows.append(f"对应调出腿={linked_text}")
        else:
            meta_rows.append(f"对应替代腿={linked_text}")

        why_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("why") or []))
        risk_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("risks") or []))
        check_rows = "".join(f"<li>{escape(business_text(row))}</li>" for row in (item.get("next_checks") or []))

        return (
            "<article class='card'>"
            "<div class='card-header'>"
            f"<div><h3>{escape(item.get('name') or item.get('ts_code') or '-')}</h3><div class='muted'>{escape(item.get('ts_code') or '-')} / {escape(item.get('sector') or '-')}</div></div>"
            f"<div>{badge(verdict or '-', tone)}</div>"
            "</div>"
            f"<p>{escape(business_text(item.get('summary') or '-'))}</p>"
            f"<div class='muted'>{escape('｜'.join(meta_rows))}</div>"
            f"<div style='margin-top:14px'><h4>{'为什么可以买' if side == 'buy' else '为什么要卖'}</h4><ul>{why_rows or '<li>当前没有额外说明。</li>'}</ul></div>"
            f"<div style='margin-top:14px'><h4>主要风险</h4><ul>{risk_rows or '<li>当前没有额外风险提示。</li>'}</ul></div>"
            f"<div style='margin-top:14px'><h4>{'下单前再看' if side == 'buy' else '继续核对'}</h4><ul>{check_rows or '<li>当前没有额外检查项。</li>'}</ul></div>"
            "</article>"
        )

    buy_candidates = decision.get("buy_candidates") or []
    if buy_candidates:
        buy_section = (
            "<section class='panel'>"
            "<h2>买入侧</h2>"
            "<div class='section-intro'>这里不是“想不想买”，而是“在当前风控口径下能不能买、适合怎么买”。</div>"
            + "".join(render_trade_card(item, "buy") for item in buy_candidates[:5])
            + "</section>"
        )
    else:
        buy_section = (
            "<section class='panel'>"
            "<h2>买入侧</h2>"
            "<div class='card'><h3>当前没有买入候选</h3><p>这一轮没有形成可读的买入风控结论。</p></div>"
            "</section>"
        )

    sell_candidates = decision.get("sell_candidates") or []
    if sell_candidates:
        sell_section = (
            "<section class='panel'>"
            "<h2>卖出侧</h2>"
            "<div class='section-intro'>先处理该卖和该减的，再决定今天能不能去做新的进攻。</div>"
            + "".join(render_trade_card(item, "sell") for item in sell_candidates[:6])
            + "</section>"
        )
    else:
        sell_section = (
            "<section class='panel'>"
            "<h2>卖出侧</h2>"
            "<div class='card'><h3>当前没有卖出候选</h3><p>这一轮没有形成可读的卖出风控结论。</p></div>"
            "</section>"
        )

    if alerts:
        alert_cards = []
        for item in alerts[:6]:
            alert_cards.append(
                "<article class='card'>"
                "<div class='card-header'>"
                f"<div><h3>{escape(code_label(item.get('alert_type') or 'risk_alert'))}</h3><div class='muted'>{escape(item.get('alert_time') or '-')}</div></div>"
                f"<div>{badge(item.get('severity'), 'warning')}</div>"
                "</div>"
                f"<p>{escape(business_text(item.get('message') or '-'))}</p>"
                f"<div class='muted'>对象：{escape(item.get('ts_code') or '全组合')}</div>"
                f"<div class='muted'>建议动作：{escape(business_text(item.get('action') or '-'))}</div>"
                "</article>"
            )
        alert_section = (
            "<section class='panel'>"
            "<h2>最近预警</h2>"
            "<div class='section-intro'>如果组合状态变差，通常会先在这里留下直接预警。</div>"
            f"{''.join(alert_cards)}"
            "</section>"
        )
    else:
        alert_section = ""

    body = render_market_fact_panel(overview, capital, "风险页事实口径") + decision_summary + buy_section + sell_section + alert_section
    return render_shell(
        page_title="SMR 风险结果",
        current_path="/risk",
        hero_title="买卖决策风控",
        hero_subtitle="把风险控制翻译成老板今天能不能买、该不该卖的结论。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("组合状态", decision.get("portfolio_state_label") or code_label(decision.get("portfolio_state") or risk.get("status") or "-")),
            ("买入候选", decision.get("buy_candidate_count") or 0),
            ("卖出候选", decision.get("sell_candidate_count") or 0),
            ("风险预警", len(alerts)),
            ("两融事实日", capital.get("margin_balance", {}).get("anchor_trade_date") or "-"),
            ("互联互通日频", capital.get("stock_connect", {}).get("anchor_trade_date") or "-"),
        ],
        **shell_state_kwargs(state),
    )


def render_capital_flow_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state["capital_flow"]
    margin = capital["margin_balance"]
    stock_connect = capital["stock_connect"]

    margin_exchange_dates = margin.get("exchange_trade_dates") or {}
    margin_exchange_counts = margin.get("counts_by_exchange") or {}
    stock_connect_market_dates = stock_connect.get("market_trade_dates") or {}
    stock_connect_holding_dates = stock_connect.get("holding_trade_dates") or {}
    stock_connect_route_counts = stock_connect.get("holding_counts_by_route") or {}
    route_realtime_probe = stock_connect.get("route_realtime_probe") or {}
    northbound_estimate_summary = stock_connect.get("northbound_estimate_summary") or []
    northbound_estimated_count = sum(1 for item in northbound_estimate_summary if item.get("estimated"))
    margin_focus_hits = margin.get("focus_hits") or []
    stock_connect_focus_hits = stock_connect.get("focus_hits") or []
    market_summaries = stock_connect.get("market_summaries") or []

    margin_rows = []
    for index, item in enumerate(margin_focus_hits, start=1):
        margin_rows.append(
            [
                (
                    f"{render_rank_badge(index)}"
                    f"<div style='display:inline-block; margin-left:10px'>"
                    f"<strong>{escape(item.get('security_name') or item.get('ts_code') or '-')}</strong>"
                    f"<div class='muted'>{escape(item.get('ts_code') or '-')} · {escape(code_label(item.get('exchange')))}</div>"
                    "</div>"
                ),
                render_pool_badges(item.get("pool_types")),
                escape(fmt_money_cn(item.get("financing_balance"))),
                escape(fmt_money_cn(item.get("financing_buy_amount"))),
                escape(fmt_shares_cn(item.get("securities_lending_balance_volume"))),
                escape(fmt_money_cn(item.get("margin_total_balance"))),
            ]
        )

    stock_connect_rows = []
    for index, item in enumerate(stock_connect_focus_hits, start=1):
        stock_connect_rows.append(
            [
                (
                    f"{render_rank_badge(index)}"
                    f"<div style='display:inline-block; margin-left:10px'>"
                    f"<strong>{escape(item.get('security_name') or item.get('ts_code') or '-')}</strong>"
                    f"<div class='muted'>{escape(item.get('ts_code') or '-')} · {escape(item.get('trade_date') or '-')}</div>"
                    "</div>"
                ),
                render_pool_badges(item.get("pool_types")),
                escape(item.get("route_name") or "-"),
                escape(code_label(item.get("direction"))),
                escape(fmt_shares_cn(item.get("holding_quantity"))),
            ]
        )

    market_summary_rows = []
    for item in market_summaries:
        market_summary_rows.append(
            [
                escape(item.get("route_name") or "-"),
                escape(code_label(item.get("direction"))),
                escape(item.get("trade_date") or "-"),
                escape(item.get("currency") or "-"),
                escape(fmt_money_cn(item.get("buy_amount"))),
                escape(fmt_money_cn(item.get("sell_amount"))),
                escape(fmt_money_cn(item.get("total_amount"))),
                escape(stock_connect_basis_text(item)),
            ]
        )

    probe_rows = []
    market_summary_map = {item.get("route_key"): item for item in market_summaries}
    for route_key in ("northbound_sh", "northbound_sz"):
        probe = route_realtime_probe.get(route_key) or {}
        item = market_summary_map.get(route_key) or {}
        refill_text = "已回填到事实日" if item.get("buy_sell_estimated") else stock_connect_estimate_reason_text(
            item.get("estimate_unavailable_reason")
        )
        probe_rows.append(
            [
                escape(item.get("route_name") or code_label(route_key)),
                escape(probe.get("trade_date") or "-"),
                badge(probe.get("status_label") or "未拿到", "ghost"),
                escape(fmt_money_cn(probe.get("net_buy_amount"))),
                escape(fmt_money_cn(probe.get("buy_sell_amount"))),
                escape(fmt_money_cn(item.get("buy_amount"))),
                escape(fmt_money_cn(item.get("sell_amount"))),
                escape(refill_text),
            ]
        )

    body = (
        f"{render_market_fact_panel(overview, capital, '资金流事实口径总览')}"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>两融快照</h2>"
        "<div class='section-intro'>按本轮官方已落地的最新事实日期展示；如果当天部分交易所还没放数，以下面实际日期为准。</div>"
        f"<div class='info-grid'>{render_kv_chips([('最新事实日期', margin.get('anchor_trade_date')), ('命中关注标的', margin.get('active_universe_hit_count')), ('明细行数', margin.get('detail_row_count'))])}</div>"
        f"<div class='muted' style='margin-top:14px'>各交易所实际日期</div>"
        f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips(list(margin_exchange_dates.items())) if margin_exchange_dates else ''}</div>"
        f"<div class='muted' style='margin-top:14px'>明细覆盖行数</div>"
        f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips(list(margin_exchange_counts.items())) if margin_exchange_counts else ''}</div>"
        "<div class='source-link'>"
        f"{link_for_artifact(margin.get('artifact'))}"
        "</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>互联互通快照</h2>"
        "<div class='section-intro'>最新事实日期只看四条日频成交路线；北向买卖拆分另走实时试探，不和历史事实日强行混写。</div>"
        f"<div class='info-grid'>{render_kv_chips([('最新事实日期', stock_connect.get('anchor_trade_date')), ('命中关注标的', stock_connect.get('active_universe_hit_count')), ('持仓行数', stock_connect.get('holding_row_count')), ('北向已回填', f'{northbound_estimated_count}/2')])}</div>"
        f"<div class='muted' style='margin-top:14px'>日频路线实际日期</div>"
        f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips(list(stock_connect_market_dates.items())) if stock_connect_market_dates else ''}</div>"
        f"<div class='muted' style='margin-top:14px'>持股数据实际日期</div>"
        f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips(list(stock_connect_holding_dates.items())) if stock_connect_holding_dates else ''}</div>"
        f"<div class='muted' style='margin-top:14px'>持股明细覆盖行数</div>"
        f"<div class='info-grid' style='margin-top:10px'>{render_kv_chips(list(stock_connect_route_counts.items())) if stock_connect_route_counts else ''}</div>"
        + (
            f"<div class='muted' style='margin-top:14px'>{escape(business_text(stock_connect.get('probe_line') or ''))}</div>"
            if stock_connect.get("probe_line")
            else ""
        )
        + (
            f"<div class='muted' style='margin-top:8px'>{escape(business_text(stock_connect.get('estimate_line') or ''))}</div>"
            if stock_connect.get("estimate_line")
            else ""
        )
        + 
        "<div class='source-link'>"
        f"{link_for_artifact(stock_connect.get('artifact'))}"
        "</div>"
        "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>两融关注标的排行</h2>"
        "<div class='section-intro'>按最新融资余额从高到低，只保留当前关注池命中的标的。</div>"
        f"{render_html_table(['标的', '所在池', '融资余额', '融资买入额', '融券余量', '融资融券余额'], margin_rows, '当前没有两融命中标的。')}"
        "</article>"
        "<article class='panel'>"
        "<h2>互联互通关注标的排行</h2>"
        "<div class='section-intro'>按持股数量排序，直接看北向/南向资金当前最重的关注对象。</div>"
        f"{render_html_table(['标的', '所在池', '路线', '方向', '持股数量'], stock_connect_rows, '当前没有互联互通命中标的。')}"
        "</article>"
        "</section>"
        "<section class='panel'>"
        "<h2>北向实时试探</h2>"
        "<div class='section-intro'>这块单独展示今天实时探针看到的北向净买额和成交额；只有实时试探日期和官方事实日一致时，才会把估算买卖额回填到上面的事实表。</div>"
        f"{render_html_table(['路线', '试探日期', '当前状态', '净买额', '实时成交额', '估算买入额', '估算卖出额', '回填结果'], probe_rows, '当前没有北向实时试探结果。')}"
        "</section>"
        "<section class='panel'>"
        "<h2>互联互通路线汇总</h2>"
        "<div class='section-intro'>这部分只看官方事实日路线汇总；如果北向买卖额是估算值，会在最后一列明确标出来。</div>"
        f"{render_html_table(['路线', '方向', '交易日', '币种', '买入额', '卖出额', '总成交额', '口径'], market_summary_rows, '当前没有路线汇总。')}"
        "</section>"
    )
    return render_shell(
        page_title="SMR 资金流",
        current_path="/capital-flow",
        hero_title="资金流",
        hero_subtitle="把两融和互联互通单独放到这一页，便于你专门看资金面结果。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("两融命中", margin.get("active_universe_hit_count") or 0),
            ("互联互通命中", stock_connect.get("active_universe_hit_count") or 0),
            ("两融最新事实日", margin.get("anchor_trade_date") or "-"),
            ("北向已回填", f"{northbound_estimated_count}/2"),
        ],
        **shell_state_kwargs(state),
    )


def render_events_page(state: dict, refresh_seconds: int) -> str:
    overview = state.get("overview") or {}
    capital = state.get("capital_flow") or {}
    events = state["events"]
    market_event_snapshot = events["market_event_snapshot"]
    event_calendar_snapshot = events["event_calendar_snapshot"]
    upcoming_event_calendar_snapshot = events.get("upcoming_event_calendar_snapshot") or {}
    recent_by_family = events.get("recent_market_events_by_family") or {}
    upcoming_events = events.get("upcoming_market_events") or []

    counts_by_family = market_event_snapshot.get("counts_by_family") or {}
    family_grid = (
        render_kv_chips([(code_label(key), value) for key, value in counts_by_family.items()])
        if counts_by_family
        else "<div class='empty'>暂无事件分类统计。</div>"
    )

    body = (
        f"{render_market_fact_panel(overview, capital, '事件页事实口径')}"
        "<section class='panel'>"
        "<h2>事件总览</h2>"
        "<div class='section-intro'>这里把最新事件按公告、研报、资讯拆开看，避免所有内容混成一张流水表。</div>"
        f"<div class='info-grid'>{family_grid}</div>"
        "</section>"
        "<section class='panel'>"
        "<h2>未来催化</h2>"
        "<div class='section-intro'>这一块只看接下来明确会发生什么，比如财报、电话会、分红到账、股东会和公开路演。</div>"
        f"{render_event_family_panel('近端催化日历', '按时间先后列出最近要发生的明确催化。', upcoming_events)}"
        "</section>"
        "<section class='event-grid'>"
        f"{render_event_family_panel('公告', '优先看制度性披露、公司公告和正式文件。', recent_by_family.get('announcement') or [])}"
        f"{render_event_family_panel('研报', '集中看最近新增的卖方研报和结构化研报产物。', recent_by_family.get('research') or [])}"
        f"{render_event_family_panel('资讯', '看媒体资讯和资讯搜索快照，感知当下舆情密度。', recent_by_family.get('news') or [])}"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>完整事件时间线</h2>"
        "<div class='section-intro'>如果要回看更长窗口、更多标的和完整时间线，从这里打开。</div>"
        f"<div>{link_for_artifact(event_calendar_snapshot.get('artifact'))}</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>未来催化抽取快照</h2>"
        "<div class='section-intro'>如果要核对未来催化是从哪段原文里抽出来的，从这里打开。</div>"
        f"<div>{link_for_artifact(upcoming_event_calendar_snapshot.get('artifact'))}</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>事件归一化快照</h2>"
        "<div class='section-intro'>如果要核对事件归并结果和原始归类口径，从这里打开。</div>"
        f"<div>{link_for_artifact(market_event_snapshot.get('artifact'))}</div>"
        "</article>"
        "</section>"
    )
    return render_shell(
        page_title="SMR 事件",
        current_path="/events",
        hero_title="事件",
        hero_subtitle="把事件日历、资讯和研报类事件单独放在一页，避免和其他业务结果混看。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("事件总数", event_calendar_snapshot.get("event_count") or 0),
            ("未来催化", event_calendar_snapshot.get("upcoming_event_count") or 0),
            ("跟踪标的", event_calendar_snapshot.get("tracked_symbol_count") or 0),
            ("最新事件", len(events.get("recent_market_events") or [])),
            ("两融事实日", capital.get("margin_balance", {}).get("anchor_trade_date") or "-"),
            ("互联互通日频", capital.get("stock_connect", {}).get("anchor_trade_date") or "-"),
        ],
        **shell_state_kwargs(state),
    )


def render_artifact_page(path_value: str) -> tuple[int, str]:
    artifact_path = resolve_project_path(path_value)
    if artifact_path is None:
        return 400, "<h1>无效路径</h1><p>只允许访问项目目录内的文件。</p>"
    if not artifact_path.exists() or not artifact_path.is_file():
        return 404, "<h1>文件不存在</h1><p>指定产物当前不存在。</p>"

    try:
        content = artifact_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = artifact_path.read_text(encoding="utf-8", errors="replace")

    if artifact_path.suffix.lower() in {".md", ".markdown"}:
        content_html = render_markdown_block(content)
    else:
        content_html = f"<pre>{escape(content)}</pre>"

    body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(artifact_path.name))}</title>
  <style>
    body {{
      margin: 0;
      background: #f3efe7;
      color: #1f272e;
      font-family: "PingFang SC", "Noto Serif SC", "Hiragino Sans GB", Georgia, serif;
    }}
    .page {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 24px 20px 80px;
    }}
    .panel {{
      background: rgba(255, 252, 248, 0.92);
      border: 1px solid rgba(31, 39, 46, 0.1);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 18px 42px rgba(31, 39, 46, 0.08);
    }}
    a {{ color: #114a72; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code, pre {{
      font-family: "SFMono-Regular", "JetBrains Mono", Menlo, monospace;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      background: rgba(31, 39, 46, 0.05);
      border-radius: 18px;
      padding: 18px;
      border: 1px solid rgba(31, 39, 46, 0.08);
      overflow: auto;
      font-family: "SFMono-Regular", "JetBrains Mono", Menlo, monospace;
    }}
    .muted {{ color: #6d7579; }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid rgba(31, 39, 46, 0.08);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.72);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 10px;
      text-align: left;
      border-bottom: 1px solid rgba(31, 39, 46, 0.08);
      vertical-align: top;
    }}
    th {{
      color: #6d7579;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .markdown-body {{
      font-size: 15px;
      line-height: 1.68;
    }}
    .markdown-body > :first-child {{
      margin-top: 0;
    }}
    .markdown-body > :last-child {{
      margin-bottom: 0;
    }}
    .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5 {{
      margin: 1.15rem 0 0.65rem;
      line-height: 1.28;
    }}
    .markdown-body h2 {{ font-size: 28px; }}
    .markdown-body h3 {{ font-size: 22px; }}
    .markdown-body h4 {{ font-size: 18px; }}
    .markdown-body h5 {{ font-size: 16px; color: #6d7579; }}
    .markdown-body p {{ margin: 0 0 0.95rem; }}
    .markdown-body ul, .markdown-body ol {{
      margin: 0 0 1rem 1.25rem;
      padding: 0;
    }}
    .markdown-body li {{ margin-bottom: 0.45rem; }}
    .markdown-body blockquote {{
      margin: 0 0 1rem;
      padding: 0.9rem 1rem;
      border-left: 4px solid rgba(17, 74, 114, 0.22);
      background: rgba(17, 74, 114, 0.06);
      border-radius: 0 16px 16px 0;
      color: #284455;
    }}
    .markdown-body code {{
      padding: 0.1rem 0.36rem;
      border-radius: 8px;
      background: rgba(31, 39, 46, 0.08);
      font-size: 0.92em;
    }}
    .md-rule {{
      border: 0;
      border-top: 1px solid rgba(31, 39, 46, 0.1);
      margin: 1rem 0 1.1rem;
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="panel">
      <p><a href="/">返回业务导航</a></p>
      <h1>{escape(str(artifact_path.name))}</h1>
      <p class="muted">{escape(str(artifact_path))}</p>
      {content_html}
    </div>
  </div>
</body>
</html>"""
    return 200, body


def safe_json(raw: str | None, default):
    try:
        return json.loads(raw or "")
    except (TypeError, json.JSONDecodeError):
        return default


def review_db_rows(limit: int = 80) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_decision_tables(conn)
        rows = conn.execute(
            """
            SELECT recommendation_id, ticker, market, theme, action, status, decision_time,
                   suggested_position_pct, max_position_pct, thesis_summary, data_health_snapshot_json,
                   evidence_check_snapshot_json, lint_snapshot_json, risk_snapshot_json,
                   human_review_status, reviewer, review_comment, metadata_json, updated_at
            FROM decision_ledger
            ORDER BY datetime(updated_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "recommendation_id": row[0],
            "ticker": row[1],
            "market": row[2],
            "theme": row[3],
            "action": row[4],
            "status": row[5],
            "decision_time": row[6],
            "suggested_position_pct": row[7],
            "max_position_pct": row[8],
            "thesis_summary": row[9],
            "data_health_snapshot": safe_json(row[10], {}),
            "evidence_check_snapshot": safe_json(row[11], {}),
            "lint_snapshot": safe_json(row[12], {}),
            "risk_snapshot": safe_json(row[13], {}),
            "human_review_status": row[14],
            "reviewer": row[15],
            "review_comment": row[16],
            "metadata": safe_json(row[17], {}),
            "updated_at": row[18],
        }
        for row in rows
    ]


def review_db_row(recommendation_id: str) -> dict | None:
    matches = [row for row in review_db_rows(limit=300) if row.get("recommendation_id") == recommendation_id]
    return matches[0] if matches else None


def render_snapshot_pretty(value: dict | list | None, limit: int = 1800) -> str:
    text = json.dumps(value or {}, ensure_ascii=False, indent=2, default=str)
    if len(text) > limit:
        text = text[:limit].rstrip() + "\n..."
    return f"<pre class='artifact-pre'>{escape(text)}</pre>"


def review_status_label(row: dict, key: str) -> str:
    if key == "data":
        status = row.get("data_health_snapshot", {}).get("overall_status")
    elif key == "evidence":
        status = row.get("evidence_check_snapshot", {}).get("severity")
    elif key == "lint":
        status = row.get("lint_snapshot", {}).get("max_severity")
    else:
        status = row.get("status")
    return str(status or "-")


def render_review_queue(state: dict, refresh_seconds: int) -> str:
    rows = review_db_rows()
    body_rows = []
    for row in rows:
        rec_id = row.get("recommendation_id")
        href = f"/recommendation/review?id={quote(rec_id or '')}"
        body_rows.append(
            [
                escape(str(row.get("updated_at") or row.get("decision_time") or "-")),
                f"<a href='{href}'>{escape(str(row.get('ticker') or row.get('recommendation_id') or '-'))}</a>",
                escape(compact_text(row.get("theme") or "-", 30)),
                escape(compact_text(row.get("action") or "-", 56)),
                badge(row.get("status"), status_tone(row.get("status"))),
                badge(review_status_label(row, "data"), status_tone(review_status_label(row, "data"))),
                badge(review_status_label(row, "evidence"), status_tone(review_status_label(row, "evidence"))),
                badge(review_status_label(row, "lint"), status_tone(review_status_label(row, "lint"))),
            ]
        )
    body = (
        "<section class='panel'>"
        "<h2>人工审核队列</h2>"
        "<div class='section-intro'>只处理候选、观察、阻断和已审核状态；交易型建议在通过人工审核前不会进入正式 paper 结论。</div>"
        + render_html_table(
            ["更新时间", "标的/建议", "主题", "动作", "状态", "数据", "证据", "Lint"],
            body_rows,
            empty_text="当前没有进入 ledger 的建议。",
        )
        + "</section>"
    )
    return render_shell(
        page_title="SMR 审核队列",
        current_path="/review-queue",
        hero_title="投研审核队列",
        hero_subtitle="候选建议必须先看数据健康、证据图谱、lint 和风险信息，再进入人工审核动作。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[("待处理", sum(1 for row in rows if row.get("status") == "pending_human_review")), ("总数", len(rows))],
        **shell_state_kwargs(state),
    )


def render_review_action_form(row: dict) -> str:
    disabled_approval = str(row.get("status") or "").startswith("blocked")
    approve_note = "阻断状态不能 approve，只能归档或要求补研究。" if disabled_approval else "审核通过后进入 approved_paper。"
    return f"""
    <form class='review-form' method='post' action='/recommendation/review'>
      <input type='hidden' name='recommendation_id' value='{escape(str(row.get("recommendation_id") or ""), quote=True)}'>
      <label>Reviewer <input name='reviewer' value='human_reviewer'></label>
      <label>Action
        <select name='action'>
          <option value='approve_paper'>approve_paper</option>
          <option value='reject'>reject</option>
          <option value='request_more_research'>request_more_research</option>
          <option value='downgrade_to_observation'>downgrade_to_observation</option>
          <option value='reduce_position_size'>reduce_position_size</option>
          <option value='archive'>archive</option>
        </select>
      </label>
      <label>新仓位（reduce_position_size 时必填）<input name='suggested_position_pct' placeholder='例如 0.03'></label>
      <label>审核意见 <textarea name='comment' required placeholder='说明通过、拒绝或要求补研究的理由'></textarea></label>
      <p class='muted'>{escape(approve_note)}</p>
      <button type='submit'>提交审核动作</button>
    </form>
    """


def render_recommendation_review_page(
    state: dict,
    recommendation_id: str,
    refresh_seconds: int,
    message: str | None = None,
) -> tuple[int, str]:
    row = review_db_row(recommendation_id)
    if not row:
        return 404, "<h1>Review item not found</h1>"
    metadata = row.get("metadata") or {}
    claim_summary = metadata.get("claim_evidence_summary") or row.get("evidence_check_snapshot", {}).get("claim_evidence_summary")
    valuation = metadata.get("valuation_snapshot")
    consensus_proxy = metadata.get("consensus_revision_proxy")
    bear_case = metadata.get("bear_case_result")
    message_html = f"<div class='notice'>{escape(message)}</div>" if message else ""
    audit_body = (
        "<section class='grid-2'>"
        "<article class='panel'><h2>建议摘要</h2>"
        + render_kv_chips(
            [
                ("状态", row.get("status")),
                ("标的", row.get("ticker")),
                ("市场", row.get("market")),
                ("建议仓位", row.get("suggested_position_pct")),
                ("最大仓位", row.get("max_position_pct")),
            ]
        )
        + f"<p>{escape(row.get('thesis_summary') or row.get('action') or '-')}</p>"
        + "</article>"
        "<article class='panel'><h2>审核动作</h2>"
        + render_review_action_form(row)
        + "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'><h2>Data Health</h2>"
        + render_snapshot_pretty(row.get("data_health_snapshot"), 1600)
        + "</article>"
        "<article class='panel'><h2>Evidence / Lint</h2>"
        + render_snapshot_pretty({"evidence": row.get("evidence_check_snapshot"), "lint": row.get("lint_snapshot")}, 1800)
        + "</article>"
        "</section>"
        "<section class='grid-2'>"
        "<article class='panel'><h2>Claim-Evidence Summary</h2>"
        + render_snapshot_pretty(claim_summary, 1600)
        + "</article>"
        "<article class='panel'><h2>Bear / Valuation / Proxy</h2>"
        + render_snapshot_pretty({"bear_case": bear_case, "valuation": valuation, "consensus_proxy": consensus_proxy}, 1800)
        + "</article>"
        "</section>"
        "<section class='panel'><h2>Ledger Metadata</h2>"
        + render_snapshot_pretty(metadata, 2600)
        + "</section>"
    )
    body = message_html + audit_body
    return 200, render_shell(
        page_title="SMR 建议审核",
        current_path="/review-queue",
        hero_title=f"审核 {row.get('ticker') or recommendation_id}",
        hero_subtitle="这里是候选建议进入 paper 结论前的审计入口：先看状态、证据、反方和缺口，再做审核动作。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[("状态", row.get("status")), ("证据", review_status_label(row, "evidence")), ("Lint", review_status_label(row, "lint"))],
        **shell_state_kwargs(state),
    )


PAGE_RENDERERS = {
    "/": render_today_overview,
    "/coverage": render_coverage_pool,
    "/signals": render_signal_flow,
    "/research": render_research_queue,
    "/health": render_data_health,
}


def build_handler(refresh_seconds: int):
    class ControlTowerHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, content: str, content_type: str = "text/html; charset=utf-8") -> None:
            payload = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(payload)

        def _send_head(self, status: int, content_type: str = "text/html; charset=utf-8") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                state = build_dashboard_state()
                self._send(200, json.dumps(state, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
                return
            if parsed.path == "/research/item":
                state = build_dashboard_state()
                ts_code = parse_qs(parsed.query).get("ts_code", [""])[0]
                status, body = render_research_detail_page(state, ts_code, refresh_seconds)
                self._send(status, body)
                return
            if parsed.path == "/portfolio/action":
                state = build_dashboard_state()
                action_id = parse_qs(parsed.query).get("id", [""])[0]
                status, body = render_action_detail_page(state, action_id, refresh_seconds)
                self._send(status, body)
                return
            if parsed.path == "/recommendation/review":
                state = build_dashboard_state()
                recommendation_id = parse_qs(parsed.query).get("id", [""])[0]
                status, body = render_recommendation_review_page(state, recommendation_id, refresh_seconds)
                self._send(status, body)
                return
            if parsed.path == "/artifact":
                path_value = parse_qs(parsed.query).get("path", [""])[0]
                status, body = render_artifact_page(path_value)
                self._send(status, body)
                return
            if parsed.path == "/healthz":
                self._send(200, "ok", "text/plain; charset=utf-8")
                return
            renderer = PAGE_RENDERERS.get(parsed.path)
            if renderer:
                state = build_dashboard_state()
                from urllib.parse import parse_qs
                qs = parse_qs(parsed.query)
                if parsed.path == "/signals":
                    filters = {
                        "time_range": (qs.get("time_range") or ["all"])[0],
                        "source_type": (qs.get("source_type") or ["all"])[0],
                        "entity": (qs.get("entity") or ["all"])[0],
                        "strength": (qs.get("strength") or ["all"])[0],
                        "q": (qs.get("q") or [""])[0],
                    }
                    self._send(200, renderer(state, refresh_seconds, filters=filters))
                elif parsed.path == "/research":
                    filters = {
                        "priority": (qs.get("priority") or ["all"])[0],
                        "status": (qs.get("status") or ["all"])[0],
                        "sort": (qs.get("sort") or ["latest"])[0],
                        "q": (qs.get("q") or [""])[0],
                    }
                    self._send(200, renderer(state, refresh_seconds, filters=filters))
                elif parsed.path == "/coverage":
                    filters = {
                        "type": (qs.get("type") or ["all"])[0],
                        "priority": (qs.get("priority") or ["all"])[0],
                        "status": (qs.get("status") or ["all"])[0],
                        "q": (qs.get("q") or [""])[0],
                        "page": (qs.get("page") or ["1"])[0],
                    }
                    self._send(200, renderer(state, refresh_seconds, filters=filters))
                elif parsed.path == "/health":
                    filters = {
                        "status": (qs.get("status") or ["all"])[0],
                        "severity": (qs.get("severity") or ["all"])[0],
                        "q": (qs.get("q") or [""])[0],
                    }
                    self._send(200, renderer(state, refresh_seconds, filters=filters))
                else:
                    self._send(200, renderer(state, refresh_seconds))
                return
            self._send(404, "<h1>Not Found</h1>")

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/recommendation/review":
                self._send(404, "<h1>Not Found</h1>")
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            form = parse_qs(raw)
            recommendation_id = (form.get("recommendation_id") or [""])[0]
            action = (form.get("action") or [""])[0]
            reviewer = (form.get("reviewer") or [""])[0] or "human_reviewer"
            comment = (form.get("comment") or [""])[0]
            overrides = {}
            position = (form.get("suggested_position_pct") or [""])[0].strip()
            if position:
                try:
                    overrides["suggested_position_pct"] = float(position)
                except ValueError:
                    overrides["suggested_position_pct"] = position
            conn = sqlite3.connect(DB_PATH)
            try:
                result = review_recommendation(
                    conn,
                    recommendation_id=recommendation_id,
                    reviewer=reviewer,
                    action=action,
                    comment=comment,
                    overrides=overrides,
                )
                conn.commit()
                message = f"审核动作已记录：{result.get('previous_status')} -> {result.get('new_status')}"
            except Exception as exc:
                conn.rollback()
                message = f"审核动作失败：{exc}"
            finally:
                conn.close()
            state = build_dashboard_state()
            status, body = render_recommendation_review_page(state, recommendation_id, refresh_seconds, message=message)
            self._send(status, body)

        def do_HEAD(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                self._send_head(200, "application/json; charset=utf-8")
                return
            if parsed.path == "/research/item":
                state = build_dashboard_state()
                ts_code = parse_qs(parsed.query).get("ts_code", [""])[0]
                self._send_head(200 if find_watch_item(state, ts_code) else 404)
                return
            if parsed.path == "/portfolio/action":
                state = build_dashboard_state()
                action_id = parse_qs(parsed.query).get("id", [""])[0]
                self._send_head(200 if find_action(state, action_id) else 404)
                return
            if parsed.path == "/recommendation/review":
                recommendation_id = parse_qs(parsed.query).get("id", [""])[0]
                self._send_head(200 if review_db_row(recommendation_id) else 404)
                return
            if parsed.path == "/artifact":
                path_value = parse_qs(parsed.query).get("path", [""])[0]
                artifact_path = resolve_project_path(path_value)
                if artifact_path is None:
                    self._send_head(400)
                    return
                if not artifact_path.exists() or not artifact_path.is_file():
                    self._send_head(404)
                    return
                self._send_head(200)
                return
            if parsed.path in PAGE_RENDERERS or parsed.path == "/healthz":
                content_type = "text/plain; charset=utf-8" if parsed.path == "/healthz" else "text/html; charset=utf-8"
                self._send_head(200, content_type)
                return
            self._send_head(404)

        def log_message(self, format: str, *args) -> None:
            return

    return ControlTowerHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local SMR business dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", default=8877, type=int, help="HTTP bind port")
    parser.add_argument("--refresh-seconds", default=60, type=int, help="Browser auto-refresh interval")
    parser.add_argument("--dump-json", action="store_true", help="Print the aggregated state JSON and exit")
    parser.add_argument("--open-browser", action="store_true", help="Open the dashboard in the default browser")
    args = parser.parse_args()

    if args.dump_json:
        print(json.dumps(build_dashboard_state(), ensure_ascii=False, indent=2))
        return

    handler = build_handler(args.refresh_seconds)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"SMR 业务看板已启动：{url}")
    print("页面路由：/, /reports, /opportunities, /analysis, /operations, /research, /portfolio, /risk, /capital-flow, /events")
    print("状态接口：/api/state")
    print("产物查看：/artifact?path=相对路径")

    if args.open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
