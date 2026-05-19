#!/usr/bin/env python3
"""Serve the SMR business-facing dashboard locally."""

from __future__ import annotations

import argparse
import json
import re
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

from smr_dashboard import build_dashboard_state, resolve_project_path


NAV_ITEMS = [
    ("/", "导航"),
    ("/reports", "日报"),
    ("/opportunities", "机会挖掘"),
    ("/analysis", "个股分析"),
    ("/operations", "自动运营"),
    ("/research", "研究观察"),
    ("/portfolio", "调仓动作"),
    ("/risk", "风险结果"),
    ("/capital-flow", "资金流"),
    ("/events", "事件"),
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
        "purpose_text": "把异动、因子、研究池、轻量回测和攻防推演收敛成纸面观察单。",
        "deliverable_text": "更新机会雷达、策略证据、攻防推演和纸面观察单。",
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
    "paper_watch_candidate": "纸面观察候选",
    "paper_watch_ready": "纸面观察就绪",
    "watch_with_evidence": "带证据观察",
    "research_first": "先补研究",
    "monitor_only": "仅监控",
    "radar_candidate": "雷达候选",
    "paper_watch_active": "纸面观察中",
    "ready_for_paper_watch": "纸面证据通过",
    "thin_sample": "样本偏薄",
    "mixed_evidence": "证据混合",
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
    "fresh_hot": "很新",
    "usable": "还能参考",
    "aging": "开始变旧",
    "stale": "偏旧",
    "daily": "日频",
    "quarterly": "季频",
    "missing": "缺失",
    "unknown": "未知",
    "success": "成功",
    "failed": "失败",
    "error": "错误",
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
    }:
        return "warning"
    if key in {"dry_run", "watch_only", "monitor_only", "observe", "neutral", "unknown", "missing", "radar_candidate"}:
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
) -> str:
    facts_html = ""
    if hero_facts:
        facts_html = "<div class='hero-facts'>" + render_kv_chips(hero_facts, chip_class="hero-chip") + "</div>"
    refresh_meta = ""
    if refresh_seconds > 0 and not state_version:
        refresh_meta = f'  <meta http-equiv="refresh" content="{refresh_seconds}">\n'
    status_strip_html = ""
    if snapshot_generated_at or state_version:
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
      --bg: #f3efe7;
      --panel: rgba(255, 252, 248, 0.9);
      --ink: #1f272e;
      --muted: #6d7579;
      --line: rgba(31, 39, 46, 0.1);
      --brand: #114a72;
      --brand-soft: rgba(17, 74, 114, 0.08);
      --good: #165f4f;
      --warn: #a86112;
      --ghost: #546673;
      --shadow: 0 20px 48px rgba(31, 39, 46, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(16, 111, 140, 0.1), transparent 32%),
        radial-gradient(circle at top right, rgba(184, 116, 52, 0.1), transparent 30%),
        linear-gradient(180deg, #fbf8f2 0%, var(--bg) 100%);
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
      border-radius: 28px;
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
    .status-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .status-pill {{
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.76);
      box-shadow: 0 12px 28px rgba(31, 39, 46, 0.05);
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
      border-radius: 24px;
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
      border-radius: 22px;
      padding: 20px;
      border: 1px solid rgba(17, 74, 114, 0.14);
      background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(17,74,114,0.04));
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
      border-radius: 18px;
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
      border-radius: 20px;
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
    .source-link {{
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid rgba(31, 39, 46, 0.08);
    }}
    @media (max-width: 1080px) {{
      .grid-2, .grid-3, .split, .report-layout, .event-grid, .story-grid, .status-strip {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="topbar">
      <div class="brand">SMR Business Dashboard</div>
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


def render_home(state: dict, refresh_seconds: int) -> str:
    overview = state["overview"]
    opportunity_engine = state.get("opportunity_engine") or {}
    radar = opportunity_engine.get("radar") or {}
    paper_watchlist = opportunity_engine.get("paper_watchlist") or {}
    deep_analysis = state.get("deep_analysis") or {}
    analysis_forecast = state.get("analysis_forecast") or {}
    operations = state.get("operations") or {}
    scheduler = operations.get("scheduler") or {}
    reporting = state["reporting"]
    strategy = state["strategy_watch"]
    portfolio = state["portfolio_action"]
    risk = state["risk"]
    capital = state["capital_flow"]
    events = state["events"]

    latest_run = scheduler.get("latest_run") or {}
    research_names = [item.get("name") for item in (strategy.get("top_focus_items") or [])[:3] if item.get("name")]
    action_titles = [item.get("title") for item in (portfolio.get("actions") or [])[:2] if item.get("title")]
    recent_alerts = risk.get("recent_alerts") or []
    recent_events = events.get("recent_market_events") or []
    upcoming_events = events.get("upcoming_market_events") or []
    latest_run_line = (
        f"今天自动链已跑 {scheduler.get('today_run_count') or 0} 次，最新一条是 {latest_run.get('label') or latest_run.get('job_id') or '暂无'}。"
    )
    freshness_line = (
        f"A/H/US 底层行情缺口 {overview.get('a_share_expected_gap_days') or 0} / "
        f"{overview.get('hk_expected_gap_days') or 0} / {overview.get('us_expected_gap_days') or 0} 天。"
    )

    tiles = "".join(
        [
            portal_tile(
                "日报",
                "/reports",
                "只看日报和今天最重要的结论。",
                [
                    reporting.get("latest_report_title") or "当前暂无日报标题。",
                    reporting.get("latest_report_summary") or "当前暂无日报摘要。",
                ],
            ),
            portal_tile(
                "机会挖掘",
                "/opportunities",
                "基于主题深度分析，直接看当下更值得继续深挖的 A 股和美股票。",
                [
                    f"主动雷达候选 {radar.get('candidate_count') or 0} 只 / 纸面观察单 {paper_watchlist.get('ticket_count') or 0} 张。",
                    *(deep_analysis.get("overview_lines") or [])[:2],
                    f"A股候选 {deep_analysis.get('a_share_candidate_count') or 0} 只 / 美股候选 {deep_analysis.get('us_candidate_count') or 0} 只。",
                ],
            ),
            portal_tile(
                "个股分析",
                "/analysis",
                "把当前覆盖股票的短周期区间推演单独拆出来，看方向、区间和指数代理。",
                [
                    *(analysis_forecast.get("overview_lines") or [])[:2],
                    f"已推演个股 {analysis_forecast.get('equity_count') or 0} 只 / 指数代理 {analysis_forecast.get('index_proxy_count') or 0} 条。",
                ],
            ),
            portal_tile(
                "自动运营",
                "/operations",
                "集中看岗位节奏、今天已经跑出的结果，以及哪些关键数据还不够新。",
                [
                    latest_run_line,
                    f"价格区间推演最近快照 {analysis_forecast.get('created_at') or '暂无'}。",
                    freshness_line,
                ],
            ),
            portal_tile(
                "研究观察",
                "/research",
                "集中看当前应该盯的标的、理由和下一步检查项。",
                [
                    f"当前优先盯：{', '.join(research_names)}" if research_names else "当前暂无研究焦点。",
                    compact_text((strategy.get("top_focus_items") or [{}])[0].get("trend_summary"), 72),
                ],
            ),
            portal_tile(
                "调仓动作",
                "/portfolio",
                "专门展示调入调出建议、轮动对和组合动作，不混别的信息。",
                [
                    *(portfolio.get("primary_call") or [])[:2],
                    *action_titles[:1],
                ],
            ),
            portal_tile(
                "风险结果",
                "/risk",
                "只看风险结论本身。",
                [
                    compact_text(recent_alerts[0].get("message"), 88) if recent_alerts else "当前没有风险预警。",
                    compact_text(recent_alerts[1].get("message"), 88) if len(recent_alerts) > 1 else "没有新增需要人工处理的风险结果。",
                ],
            ),
            portal_tile(
                "资金流",
                "/capital-flow",
                "把两融和互联互通单独放在一个页面。",
                [
                    f"两融命中关注标的 {capital['margin_balance'].get('active_universe_hit_count') or 0} 只 / 互联互通命中 {capital['stock_connect'].get('active_universe_hit_count') or 0} 只。",
                    compact_text(capital["margin_balance"].get("fact_summary_line"), 78)
                    if capital["margin_balance"].get("fact_summary_line")
                    else "当前暂无两融事实说明。",
                    compact_text(capital["stock_connect"].get("fact_summary_line"), 78)
                    if capital["stock_connect"].get("fact_summary_line")
                    else "当前暂无互联互通事实说明。",
                ],
            ),
            portal_tile(
                "事件",
                "/events",
                "把事件日历和最新资讯单独整理，看新闻和研报时不用被别的页面打断。",
                [
                    compact_text((upcoming_events[0].get("summary") or upcoming_events[0].get("title")), 88) if upcoming_events else (compact_text(recent_events[0].get("title"), 88) if recent_events else "当前暂无事件流。"),
                    f"未来催化当前收录 {events['event_calendar_snapshot'].get('upcoming_event_count') or 0} 条。",
                ],
            ),
        ]
    )

    body = (
        "<section class='panel'>"
        "<h2>业务导航</h2>"
        "<div class='section-intro'>首页只做导航和极简提示。真正的内容都分页面展开，不再把所有结果堆在一张屏里。</div>"
        f"<div class='grid-3'>{tiles}</div>"
        "</section>"
    )
    return render_shell(
        page_title="SMR 业务看板",
        current_path="/",
        hero_title="SMR 业务看板",
        hero_subtitle="只看业务结果。日报、研究观察、调仓动作、风险结果、资金流、事件各自分页面展示。",
        body=body,
        refresh_seconds=refresh_seconds,
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
        "<h2>核心指标</h2>"
        "<div class='section-intro'>先看数据是不是新、自动链今天跑到了哪、当前风控和调仓建议收口到什么程度。</div>"
        f"{render_metric_grid(metrics)}"
        "</section>"
        "<section class='report-layout'>"
        "<div class='panel-stack'>"
        "<article class='panel'>"
        "<h2>今日最重要的结论</h2>"
        f"<div class='section-intro'>{escape(compact_text(report_summary, 180))}</div>"
        f"<div class='muted' style='margin-top:10px'>{escape(report_mode_note)}</div>"
        f"<ul>{primary_calls}</ul>"
        "<div class='source-link'>"
        f"{link_for_artifact(active_report_artifact)}"
        "</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>自动链结果</h2>"
        "<div class='section-intro'>这里不看系统细节，只看今天自动链交付了什么、最新一条跑到哪一步。</div>"
        "<div class='card'>"
        "<div class='card-header'>"
        f"<div><h3>{escape(latest_run_label)}</h3><div class='muted'>{escape(latest_run_time)}</div></div>"
        f"<div>{badge(latest_run.get('status'), status_tone(latest_run.get('status')))}</div>"
        "</div>"
        f"<div class='muted'>今日自动链共 {escape(fmt_number(scheduler.get('today_run_count') or 0))} 次。</div>"
        f"<div style='margin-top:10px'>{render_count_badges(scheduler_counts, '今天还没有自动链运行记录')}</div>"
        f"{latest_run_link_html}"
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
        hero_subtitle="这一页优先展示今天候选版和随时口径，不把旧日报直接当成今天口径。",
        body=body,
        refresh_seconds=refresh_seconds,
        hero_facts=[
            ("当前展示", f"{'正式日报' if latest_report_is_aligned else '候选版'} / {report_surface_date or '-'}"),
            ("正式日报锚点", latest_report_anchor_date or "-"),
            ("两融随时", capital["margin_balance"].get("anchor_trade_date") or "-"),
            ("互联互通随时", capital["stock_connect"].get("anchor_trade_date") or "-"),
            ("主张数量", len(portfolio.get("primary_call") or [])),
            ("官方材料", len(official_material_items)),
            ("电话会稿", len(public_transcript_items)),
            ("外部研究", len(external_research_items)),
            ("卖方参照", len(public_signal_items)),
            ("A股异动", len(market_flow_a_items)),
            ("港股异动", len(market_flow_h_items)),
            ("美股异动", len(market_flow_us_items)),
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
    paper_watchlist = opportunity_engine.get("paper_watchlist") or {}
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
        "<h2>纸面观察单</h2>"
        "<div class='section-intro'>这里只做 paper-only 观察，不产生真实交易指令。真实组合动作仍走现有组合和风控门禁。</div>"
        f"{render_paper_ticket_table(paper_watchlist.get('tickets') or [])}"
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

    related_stock_items = []
    if add_leg:
        related_stock_items.append(
            f"<li>调入对象：<a href='{research_detail_href(add_leg.get('ts_code'))}'>{escape(add_leg.get('name') or add_leg.get('ts_code') or '-')}</a><div class='muted'>{escape(add_leg.get('ts_code') or '-')} · {escape(code_label(add_leg.get('sector')))}</div></li>"
        )
    if remove_leg:
        related_stock_items.append(
            f"<li>调出对象：<a href='{research_detail_href(remove_leg.get('ts_code'))}'>{escape(remove_leg.get('name') or remove_leg.get('ts_code') or '-')}</a><div class='muted'>{escape(remove_leg.get('ts_code') or '-')} · {escape(code_label(remove_leg.get('sector')))}</div></li>"
        )
    if subject:
        related_stock_items.append(
            f"<li>复核对象：<a href='{research_detail_href(subject.get('ts_code'))}'>{escape(subject.get('name') or subject.get('ts_code') or '-')}</a><div class='muted'>{escape(subject.get('ts_code') or '-')} · {escape(code_label(subject.get('sector')))}</div></li>"
        )
    related_stock_html = f"<ul class='summary-list'>{''.join(related_stock_items)}</ul>" if related_stock_items else "<div class='empty'>当前没有直接关联标的。</div>"

    rationale_items = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("rationale") or []))
    next_checks = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("next_checks") or []))
    risk_flags = "".join(f"<li>{escape(business_text(item))}</li>" for item in (action.get("risk_flags") or []))
    source_refs = list(action.get("source_refs") or [])
    source_refs.extend(
        [
            ((state.get("portfolio_action") or {}).get("artifact") or {}).get("rel_path"),
            ((state.get("rotation") or {}).get("execution_plan_artifact") or {}).get("rel_path"),
        ]
    )
    management_quote_rows = action_management_quote_rows(state, action)
    management_quote_table_rows = []
    for row in management_quote_rows:
        management_quote_table_rows.append(
            [
                escape(row["role_label"]),
                (
                    f"<strong>{escape(row['name'])}</strong>"
                    f"<div class='muted'>{escape(row['ts_code'])}</div>"
                ),
                badge(row["status"], "neutral"),
                escape(row["status_text"]),
                link_for_rel_path(row["source_rel_path"], "查看电话会文字稿")
                if row.get("source_rel_path")
                else "<span class='muted'>暂无原文</span>",
            ]
        )
    compare_section = (
        render_symbol_compare_panel(
            "换入换出对比",
            add_leg.get("name") or add_leg.get("ts_code") or "调入腿",
            add_item,
            remove_leg.get("name") or remove_leg.get("ts_code") or "调出腿",
            remove_item,
            state,
        )
        if add_leg and remove_leg
        else ""
    )
    subject_context = detail_context_for_symbol(state, subject.get("ts_code")) if subject_item else {}
    subject_upcoming_events = (subject_context.get("upcoming_events") or []) if subject_item else []
    subject_context_section = (
        "<section class='grid-3'>"
        f"{render_symbol_events_panel(subject_upcoming_events, '对象未来催化')}"
        f"{render_symbol_events_panel(subject_context.get('recent_events') or [], '对象最近事件')}"
        f"{render_symbol_capital_flow_panel(subject_context)}"
        f"{render_symbol_risk_panel(subject_context)}"
        "</section>"
        if subject_item
        else ""
    )

    body = (
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>动作结论</h2>"
        f"<div class='section-intro'>{escape(business_text(action.get('summary') or '-'))}</div>"
        f"<div class='muted'>当前阶段：{escape(code_label(action.get('gate_status')))}</div>"
        f"<div class='muted'>参照金额：{escape(fmt_money_cn(action.get('trade_amount')))} / 占比：{escape(fmt_ratio(action.get('trade_amount_pct')))}</div>"
        "</article>"
        "<article class='panel'>"
        "<h2>关联标的</h2>"
        "<div class='section-intro'>从这里可以继续点进调入腿、调出腿或复核对象的研究详情。</div>"
        f"{related_stock_html}"
        "</article>"
        "</section>"
        "<section class='panel'>"
        "<h2>管理层原话状态</h2>"
        "<div class='section-intro'>这层只回答这条动作有没有足够新的管理层原话可以核对，避免把二手解读误当一手表述。</div>"
        f"{render_html_table(['角色', '对象', '原话状态', '这代表什么', '原文'], management_quote_table_rows, '当前没有关联到可判断原话状态的标的。')}"
        "</section>"
        f"{compare_section}"
        f"{subject_context_section}"
        "<section class='grid-2'>"
        "<article class='panel'>"
        "<h2>动作依据</h2>"
        f"<ul>{rationale_items or '<li>-</li>'}</ul>"
        "</article>"
        "<article class='panel'>"
        "<h2>主要风险</h2>"
        f"<ul>{risk_flags or '<li>-</li>'}</ul>"
        "</article>"
        "</section>"
        "<section class='panel'>"
        "<h2>执行前检查</h2>"
        "<div class='section-intro'>这里只放真正需要你在推进前再核对一遍的事项。</div>"
        f"<ul>{next_checks or '<li>-</li>'}</ul>"
        "</section>"
        "<section class='panel'>"
        "<h2>支撑材料</h2>"
        "<div class='section-intro'>执行计划、组合动作备忘和关联研究原文都从这里进入。</div>"
        f"{render_source_list(source_refs, '当前没有关联文件。')}"
        "</section>"
    )
    return (
        200,
        render_shell(
            page_title=f"SMR 动作详情 - {action.get('title') or action_id}",
            current_path="/portfolio",
            hero_title=action.get("title") or "动作详情",
            hero_subtitle="单动作详情页。先看动作结论和阶段，再看依据、风险、执行前检查与支撑材料。",
            body=body,
            refresh_seconds=refresh_seconds,
            hero_facts=[
                ("动作类型", code_label(action.get("action_type"))),
                ("优先级", code_label(action.get("priority"))),
                ("当前阶段", code_label(action.get("gate_status"))),
                ("参照金额", fmt_money_cn(action.get("trade_amount"))),
                ("原话状态", action_management_quote_fact(state, action)),
            ],
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


PAGE_RENDERERS = {
    "/": render_home,
    "/reports": render_reports_page,
    "/opportunities": render_opportunities_page,
    "/analysis": render_analysis_page,
    "/operations": render_operations_page,
    "/research": render_research_page,
    "/portfolio": render_portfolio_page,
    "/risk": render_risk_page,
    "/capital-flow": render_capital_flow_page,
    "/events": render_events_page,
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
                self._send(200, renderer(state, refresh_seconds))
                return
            self._send(404, "<h1>Not Found</h1>")

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
