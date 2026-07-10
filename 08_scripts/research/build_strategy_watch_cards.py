#!/usr/bin/env python3
"""Build per-stock strategy watch cards from the latest objective monitor snapshot."""

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
from smr_flow_event_digest import build_symbol_flow_event_digest, short_title
from smr_official_materials import summarize_official_materials
from smr_paths import env_or_project_path, relative_to_project
from smr_public_analyst_digest import summarize_public_analyst_signal
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run

OUTPUT_ROOT = env_or_project_path("SMR_STRATEGY_WATCH_DIR", "02_research", "strategy_watch")

PUBLIC_SIGNAL_LABELS = {
    "supportive_strong": "卖方强支撑",
    "supportive": "卖方支撑",
    "neutral_watch": "卖方中性偏跟踪",
    "neutral": "卖方中性",
    "stretched": "卖方提示偏透支",
    "cautious": "卖方偏谨慎",
    "missing": "缺失",
    "not_applicable": "不适用",
}

DISPLAY_LABELS = {
    "recommended": "推荐池",
    "candidate": "候选池",
    "watchlist": "观察池",
    "portfolio_seed": "持仓参照层",
    "seed": "种子池",
    "trend_follow": "趋势跟随",
    "trend_positive": "趋势偏正",
    "observe": "观察",
    "repair_needed": "等待修复",
    "high": "高",
    "medium": "中",
    "low": "低",
    "trend_strong": "趋势强",
    "trend_hot": "短线偏热",
    "repair_below_ma20": "20日线下修复",
    "under_ma60": "60日线下方",
    "neutral_observe": "中性观察",
    "fresh": "较新",
    "usable": "还能参考",
    "aging": "开始变旧",
    "stale": "偏旧",
    "missing": "缺失",
    "unknown": "未知",
    "ma20_above_ma60": "20日线位于60日线上方",
    "ma20_below_ma60": "20日线仍在60日线下",
    "earnings_pressure": "盈利承压",
    "earnings_growth": "盈利增长",
    "revenue_growth": "营收增长",
    "revenue_pressure": "营收承压",
    "rich_valuation": "高估值压力",
    "short_term_hot": "短线过热",
    "research_stale": "研究偏旧",
    "external_view_positive": "外部观点积极",
    "external_view_muted": "外部预期有限",
    "research_structured": "结构化研报",
    "research_table_structured": "结构化研报表",
    "research_pdf_text": "研报PDF文本",
    "research_article": "研报正文",
    "research_pdf": "研报PDF",
    "announcement": "公告",
    "ir_material_page": "投关材料页面",
    "ir_material_pdf": "投关材料PDF",
    "sec_earnings_material": "SEC业绩材料",
    "semiconductor_photonics": "光通信",
    "semiconductor_compute": "算力链",
    "ai_agent": "AI Agent",
    "embodied_ai": "具身智能",
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


def display_join(values):
    labels = [display_label(value) for value in (values or []) if value not in (None, "")]
    return "、".join(labels) if labels else "-"


def yes_no(value):
    return "是" if bool(value) else "否"


def parse_date_prefix(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def supports_public_analyst_signal(ts_code):
    text = str(ts_code or "").upper()
    return bool(text) and not text.endswith((".SZ", ".SH", ".BJ"))


def load_objective_monitor_entry(conn, entity_id=None):
    if entity_id:
        entry = get_latest_registry_entry(conn, "stock_objective_monitor_snapshot", entity_id)
        if entry is None:
            raise SystemExit(f"stock_objective_monitor_snapshot not found for entity_id: {entity_id}")
        return entry

    row = conn.execute(
        """
        SELECT id
        FROM task_registry_entity_latest
        WHERE entity_type='stock_objective_monitor_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        raise SystemExit("stock_objective_monitor_snapshot not found")
    entry = get_registry_entry_by_id(conn, row[0])
    if entry is None:
        raise SystemExit("latest stock_objective_monitor_snapshot entry missing")
    return entry


def summarize_trend_state(item):
    trend_strength = safe_float(item.get("trend_strength")) or 0.0
    rsi_14 = safe_float(item.get("rsi_14"))
    close = safe_float(item.get("latest_close"))
    ma20 = safe_float(item.get("ma_20"))
    ma60 = safe_float(item.get("ma_60"))

    if trend_strength >= 3 and rsi_14 is not None and rsi_14 >= 75:
        return {
            "label": "trend_hot",
            "summary": "趋势很强，但短线已经偏热，重点看回踩承接。",
        }
    if trend_strength >= 3 and ma20 is not None and ma60 is not None and ma20 > ma60:
        return {
            "label": "trend_strong",
            "summary": "趋势强且均线结构顺，优先看主线延续。",
        }
    if trend_strength >= 2:
        return {
            "label": "trend_positive",
            "summary": "趋势偏正向，但还需要继续确认站稳。",
        }
    if close is not None and ma20 is not None and close < ma20:
        return {
            "label": "repair_below_ma20",
            "summary": "价格还在 20 日线下方，先观察修复而不是先强化结论。",
        }
    if ma20 is not None and ma60 is not None and ma20 <= ma60:
        return {
            "label": "under_ma60",
            "summary": "中期均线还没完全修好，仍以观察和修复确认优先。",
        }
    return {
        "label": "neutral_observe",
        "summary": "没有明显强趋势优势，保持客观观察。",
    }


def summarize_valuation_pressure(item):
    pe_ttm = safe_float(item.get("pe_ttm"))
    pb = safe_float(item.get("pb"))
    if pe_ttm is None and pb is None:
        return {
            "label": "unknown",
            "summary": "暂时拿不到可直接比较的估值口径。",
        }
    if (pe_ttm is not None and pe_ttm >= 100) or (pb is not None and pb >= 10):
        return {
            "label": "high",
            "summary": "估值压力偏高，后续更需要业绩和订单兑现来托住。",
        }
    if (pe_ttm is not None and pe_ttm >= 50) or (pb is not None and pb >= 5):
        return {
            "label": "medium",
            "summary": "估值不算便宜，观察时要一起看兑现速度。",
        }
    return {
        "label": "low",
        "summary": "估值压力暂时不算主要矛盾。",
    }


def summarize_research_staleness(item):
    research = item.get("external_research") or {}
    published_dt = parse_date_prefix(research.get("published_at"))
    if published_dt is None:
        return {
            "label": "missing",
            "age_days": None,
            "summary": "当前缺少可直接复核的公开研报锚点。",
        }

    age_days = (datetime.now() - published_dt).days
    if age_days <= 45:
        label = "fresh"
        summary = "公开研报还比较新，可以继续作为辅助锚点。"
    elif age_days <= 120:
        label = "usable"
        summary = "公开研报还能参考，但要结合最新公告与价格结构。"
    elif age_days <= 180:
        label = "aging"
        summary = "公开研报开始变旧，后续更应依赖公告、季报和价格结构。"
    else:
        label = "stale"
        summary = "公开研报已经偏旧，需要尽快补更新来源。"
    return {
        "label": label,
        "age_days": age_days,
        "summary": summary,
    }


def build_next_check_items(
    item,
    trend_state,
    valuation_pressure,
    research_staleness,
    official_material=None,
    public_analyst_signal=None,
    flow_event_digest=None,
):
    tags = set(item.get("signal_tags") or [])
    results = []
    public_signal_supported = supports_public_analyst_signal(item.get("ts_code"))
    public_transcript = item.get("public_transcript") or {}

    if item.get("objective_view") == "repair_needed" or "below_ma20" in tags:
        results.append("确认价格能否重新站上 MA20，并观察量能是否配合。")
    if "ma20_below_ma60" in tags:
        results.append("继续盯 MA20 和 MA60 的乖离能否收敛，至少先停止继续走弱。")
    if "short_term_hot" in tags or trend_state["label"] == "trend_hot":
        results.append("盯 1 到 3 个交易日的回踩承接，避免把过热直接当成新加速。")
    if valuation_pressure["label"] in {"high", "medium"}:
        results.append("把估值和订单、业绩兑现速度放在一起看，别只看情绪抬估值。")
    if research_staleness["label"] in {"missing", "aging", "stale"}:
        results.append("补最新公告、季报或公开研报，让外部研究锚点尽快跟上。")
    official_label = (official_material or {}).get("freshness_label")
    if official_label in {"missing", "stale"}:
        results.append("补最近一期官方一手材料，优先看公告、电话会稿、演示稿和季报。")
    transcript_label = public_transcript.get("freshness_label")
    if transcript_label in {"missing", "stale"}:
        results.append("补最近电话会文字稿或管理层原话锚点，避免只靠公告摘要和二手解读。")
    elif transcript_label in {"fresh", "usable"} and item.get("objective_view") in {"trend_follow", "trend_positive"}:
        results.append("翻一遍最近电话会原话，确认管理层对订单、指引和节奏的表述是否继续强化。")
    analyst_label = (public_analyst_signal or {}).get("stance_label")
    if analyst_label in {"stretched", "cautious"}:
        results.append("结合外部卖方观点和估值水平，确认市场预期是否已充分反映。")
    elif analyst_label == "missing" and public_signal_supported:
        results.append("补一份公开卖方一致预期口径，至少知道市场大致怎么定价。")
    if "earnings_pressure" in tags:
        results.append("核对利润端修复是否真实发生，重点看毛利率、费用率和订单兑现。")
    if item.get("objective_view") in {"trend_follow", "trend_positive"}:
        results.append("跟踪主线催化能否延续到下一交易日，重点看放量后的承接质量。")
    pct_chg = safe_float(item.get("latest_pct_chg"))
    if pct_chg is not None and abs(pct_chg) >= 8:
        results.append("检查这次大幅波动是趋势延续，还是单日消息刺激后的短线放大。")
    upcoming_events = (flow_event_digest or {}).get("upcoming_event_calendar") or []
    if upcoming_events:
        next_event = upcoming_events[0]
        event_date = next_event.get("event_date") or "-"
        calendar_kind = next_event.get("calendar_kind") or next_event.get("event_type") or "日历事件"
        results.append(f"把 {event_date} 这个近端催化排进检查清单，重点盯 {calendar_kind} 前后的价格和原文更新。")
    for watchpoint in ((flow_event_digest or {}).get("watchpoints") or [])[:2]:
        results.append(watchpoint)

    if not results:
        results.append("暂时没有新的硬触发，保持日常跟踪并等待更强证据。")
    return ordered_unique(results)[:4]


def compute_priority(
    item,
    trend_state,
    valuation_pressure,
    research_staleness,
    official_material=None,
    public_analyst_signal=None,
    flow_event_digest=None,
):
    objective_view = item.get("objective_view")
    public_signal_supported = supports_public_analyst_signal(item.get("ts_code"))
    public_transcript = item.get("public_transcript") or {}
    score = {
        "repair_needed": 4,
        "trend_follow": 4,
        "trend_positive": 3,
        "observe": 2,
    }.get(objective_view, 1)

    if trend_state["label"] in {"trend_hot", "repair_below_ma20"}:
        score += 1
    if valuation_pressure["label"] == "high":
        score += 1
    if research_staleness["label"] in {"missing", "stale"}:
        score += 1
    official_label = (official_material or {}).get("freshness_label")
    if official_label == "missing":
        score += 1
    elif official_label in {"fresh_hot", "fresh"}:
        score += 0.5
    transcript_label = public_transcript.get("freshness_label")
    if transcript_label == "missing":
        score += 0.8
    elif transcript_label in {"fresh", "usable"} and objective_view in {"trend_follow", "trend_positive"}:
        score += 0.4
    analyst_label = (public_analyst_signal or {}).get("stance_label")
    if analyst_label in {"stretched", "cautious"}:
        score += 0.5
    elif public_signal_supported and analyst_label in {"supportive_strong", "supportive"} and objective_view in {"trend_follow", "trend_positive"}:
        score += 0.3
    if "earnings_pressure" in set(item.get("signal_tags") or []):
        score += 1
    pct_chg = safe_float(item.get("latest_pct_chg"))
    if pct_chg is not None and abs(pct_chg) >= 8:
        score += 1
    capital_flow_score = safe_float((flow_event_digest or {}).get("capital_flow_signal_score")) or 0.0
    event_score = safe_float((flow_event_digest or {}).get("event_signal_score")) or 0.0
    if capital_flow_score >= 1.6 and objective_view in {"trend_follow", "trend_positive"}:
        score += 0.3
    if event_score >= 1.3:
        score += 0.4

    if score >= 5:
        label = "high"
    elif score >= 3:
        label = "medium"
    else:
        label = "low"
    return {"label": label, "score": score}


def strategy_summary_item(conn, item, official_material=None, public_analyst_signal=None, public_transcript=None):
    trend_state = summarize_trend_state(item)
    valuation_pressure = summarize_valuation_pressure(item)
    research_staleness = summarize_research_staleness(item)
    official_material = official_material or {}
    public_analyst_signal = public_analyst_signal or {}
    public_transcript = public_transcript or {}
    flow_event_digest = build_symbol_flow_event_digest(conn, item.get("ts_code"))
    enriched_item = {**item, "public_transcript": public_transcript}
    next_check_items = build_next_check_items(
        enriched_item,
        trend_state,
        valuation_pressure,
        research_staleness,
        official_material,
        public_analyst_signal,
        flow_event_digest,
    )
    priority = compute_priority(
        enriched_item,
        trend_state,
        valuation_pressure,
        research_staleness,
        official_material,
        public_analyst_signal,
        flow_event_digest,
    )
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "objective_view": item.get("objective_view"),
        "priority": priority,
        "trend_state": trend_state,
        "valuation_pressure": valuation_pressure,
        "research_staleness": research_staleness,
        "watchpoints": ordered_unique(item.get("watchpoints") or []),
        "next_check_items": next_check_items,
        "latest_trade_date": item.get("latest_trade_date"),
        "latest_close": safe_float(item.get("latest_close")),
        "latest_pct_chg": safe_float(item.get("latest_pct_chg")),
        "trend_strength": safe_float(item.get("trend_strength")),
        "rsi_14": safe_float(item.get("rsi_14")),
        "ma_20": safe_float(item.get("ma_20")),
        "ma_60": safe_float(item.get("ma_60")),
        "ma_120": safe_float(item.get("ma_120")),
        "pe_ttm": safe_float(item.get("pe_ttm")),
        "pb": safe_float(item.get("pb")),
        "revenue_yoy": safe_float(item.get("revenue_yoy")),
        "net_profit_yoy": safe_float(item.get("net_profit_yoy")),
        "signal_tags": item.get("signal_tags") or [],
        "external_research": item.get("external_research") or {},
        "official_material": official_material,
        "public_analyst_signal": public_analyst_signal,
        "public_transcript": public_transcript,
        "margin_balance": flow_event_digest.get("margin_balance") or {},
        "stock_connect": flow_event_digest.get("stock_connect") or {},
        "stock_connect_hits": flow_event_digest.get("stock_connect_hits") or [],
        "recent_events": flow_event_digest.get("recent_events") or [],
        "event_calendar": flow_event_digest.get("event_calendar") or [],
        "upcoming_event_calendar": flow_event_digest.get("upcoming_event_calendar") or [],
        "capital_flow_summary": flow_event_digest.get("capital_flow_summary"),
        "event_summary": flow_event_digest.get("event_summary"),
        "auxiliary_watchpoints": flow_event_digest.get("watchpoints") or [],
        "capital_flow_signal_score": flow_event_digest.get("capital_flow_signal_score"),
        "event_signal_score": flow_event_digest.get("event_signal_score"),
    }


def summary_sort_key(item):
    pct_chg = safe_float(item.get("latest_pct_chg"))
    return (
        -(item.get("priority") or {}).get("score", 0),
        -(safe_float(item.get("trend_strength")) or 0.0),
        -(abs(pct_chg) if pct_chg is not None else 0.0),
        item.get("ts_code") or "",
    )


def format_number(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def format_pct(value, digits=2):
    if value is None:
        return "-"
    if value > 0:
        return f"+{value:.{digits}f}%"
    return f"{value:.{digits}f}%"


def public_signal_label_text(value):
    return PUBLIC_SIGNAL_LABELS.get(value, value or "-")


def card_filename(ts_code):
    return ts_code.lower().replace(".", "_") + "_strategy_watch.md"


def write_card(output_dir, created_at, batch_date, source_rel_path, item):
    card_path = output_dir / card_filename(item["ts_code"])
    research = item.get("external_research") or {}
    official = item.get("official_material") or {}
    analyst = item.get("public_analyst_signal") or {}
    public_transcript = item.get("public_transcript") or {}
    margin_balance = item.get("margin_balance") or {}
    stock_connect = item.get("stock_connect") or {}
    recent_events = item.get("recent_events") or []
    event_calendar = item.get("event_calendar") or []
    upcoming_event_calendar = item.get("upcoming_event_calendar") or []
    lines = [
        f"# {item['name']} 策略观察卡",
        "",
        f"- generated_at: {created_at}",
        f"- batch_date: {batch_date}",
        f"- ts_code: {item['ts_code']}",
        f"- sector: {display_label(item.get('sector') or '-')}",
        f"- pool_types: {display_join(item.get('pool_types'))}",
        f"- source_objective_monitor_rel_path: {source_rel_path}",
        "",
        "## 当前口径",
        "",
        f"- objective_view: {display_label(item.get('objective_view'))}",
        f"- priority: {display_label(item['priority']['label'])} / score=`{item['priority']['score']}`",
        f"- trend_state: {display_label(item['trend_state']['label'])}",
        f"- trend_state_summary: {item['trend_state']['summary']}",
        f"- valuation_pressure: {display_label(item['valuation_pressure']['label'])}",
        f"- valuation_summary: {item['valuation_pressure']['summary']}",
        f"- research_staleness: {display_label(item['research_staleness']['label'])}",
        f"- research_staleness_summary: {item['research_staleness']['summary']}",
        "",
        "## 资金与事件补充",
        "",
        f"- 资金面：{item.get('capital_flow_summary') or '当前缺少更强的官方资金流跟踪。'}",
        f"- 事件面：{item.get('event_summary') or '最近没有抓到新的事件信号。'}",
        "",
        "## 辅助链锚点",
        "",
        f"- margin_balance.trade_date: `{margin_balance.get('trade_date') or '-'}`",
        f"- margin_balance.attention: {display_label(margin_balance.get('attention_label'))}",
        f"- margin_balance.summary: {margin_balance.get('summary') or '-'}",
        f"- stock_connect.latest_trade_date: `{stock_connect.get('latest_trade_date') or '-'}`",
        f"- stock_connect.freshness: {display_label(stock_connect.get('freshness_label'))}",
        f"- stock_connect.summary: {stock_connect.get('summary') or '-'}",
        "",
        "## 关键观察点",
        "",
    ]
    for watchpoint in item.get("watchpoints") or []:
        lines.append(f"- {watchpoint}")
    if not item.get("watchpoints"):
        lines.append("- 当前暂无额外观察点，先保持日常跟踪。")

    lines.extend(
        [
            "",
            "## 下一检查项",
            "",
        ]
    )
    for value in item.get("next_check_items") or []:
        lines.append(f"- {value}")

    lines.extend(["", "## 最近事件提要", ""])
    if recent_events:
        for event in recent_events[:3]:
            lines.append(
                f"- {event.get('event_date') or '-'} / {event.get('importance') or '-'} / "
                f"{display_label(event.get('event_family'))} / {short_title(event.get('title') or '-')}"
            )
    else:
        lines.append("- 最近没有抓到新的事件提要。")

    lines.extend(["", "## 未来催化日历", ""])
    if upcoming_event_calendar:
        for event in upcoming_event_calendar[:3]:
            lines.append(
                f"- {event.get('event_date') or '-'} / {display_label(event.get('calendar_kind') or event.get('event_type'))} / "
                f"{event.get('summary') or short_title(event.get('title') or '-')}"
            )
    else:
        lines.append("- 当前还没有抽到明确的未来催化日历。")

    lines.extend(["", "## 最近日历型事件", ""])
    if event_calendar:
        for event in event_calendar[:2]:
            lines.append(
                f"- {event.get('event_date') or '-'} / {display_label(event.get('event_type'))} / "
                f"{short_title(event.get('title') or '-')}"
            )
    else:
        lines.append("- 最近没有新的 calendar-like 事件。")

    lines.extend(
        [
            "",
            "## 证据锚点",
            "",
            f"- latest_trade_date: `{item.get('latest_trade_date') or '-'}`",
            f"- latest_close / pct_chg: `{format_number(item.get('latest_close'))}` / `{format_number(item.get('latest_pct_chg'))}`",
            f"- trend_strength / rsi_14: `{format_number(item.get('trend_strength'))}` / `{format_number(item.get('rsi_14'))}`",
            f"- ma_20 / ma_60 / ma_120: `{format_number(item.get('ma_20'))}` / `{format_number(item.get('ma_60'))}` / `{format_number(item.get('ma_120'))}`",
            f"- pe_ttm / pb: `{format_number(item.get('pe_ttm'))}` / `{format_number(item.get('pb'))}`",
            f"- revenue_yoy / net_profit_yoy: `{format_number(item.get('revenue_yoy'))}` / `{format_number(item.get('net_profit_yoy'))}`",
            f"- signal_tags: {display_join(item.get('signal_tags'))}",
            f"- external_research.source_kind: {display_label(research.get('source_kind'))}",
            f"- external_research.published_at: `{research.get('published_at') or '-'}`",
            f"- external_research.org_name: `{research.get('org_name') or '-'}`",
            f"- external_research.rating_name: `{research.get('rating_name') or '-'}`",
            f"- external_research.source_rel_path: `{research.get('source_rel_path') or '-'}`",
            "",
            "## 官方一手材料",
            "",
            f"- official_material.available: {yes_no(official.get('available'))}",
            f"- official_material.item_count: `{official.get('item_count') or 0}`",
            f"- official_material.freshness_label: {display_label(official.get('freshness_label'))}",
            f"- official_material.summary: {official.get('summary') or '-'}",
            f"- official_material.latest_title: `{official.get('latest_title') or '-'}`",
            f"- official_material.latest_publish_time: `{official.get('latest_publish_time') or '-'}`",
            "",
        ]
    )
    for ref in (official.get("source_rel_paths") or [])[:3]:
        lines.append(f"- official_material.source_ref: `{ref}`")
    lines.extend(
        [
            "",
            "## 公开电话会文字稿",
            "",
            f"- public_transcript.available: {yes_no(bool(public_transcript))}",
            f"- public_transcript.freshness_label: {display_label(public_transcript.get('freshness_label'))}",
            f"- public_transcript.published_at: `{public_transcript.get('published_at') or '-'}`",
            f"- public_transcript.quarter_label: `{public_transcript.get('quarter_label') or '-'}`",
            f"- public_transcript.speaker_count: `{public_transcript.get('speaker_count') or 0}`",
            f"- public_transcript.speakers: {display_join(public_transcript.get('speakers') or [])}",
            f"- public_transcript.summary: {public_transcript.get('summary') or '-'}",
            "",
            "## 公开卖方参照",
            "",
            f"- public_analyst_signal.available: {yes_no(analyst.get('available'))}",
            f"- public_analyst_signal.stance_label: `{public_signal_label_text(analyst.get('stance_label'))}`",
            f"- public_analyst_signal.stance_summary: {analyst.get('stance_summary') or '-'}",
            f"- public_analyst_signal.mean_consensus: `{analyst.get('mean_consensus') or '-'}`",
            f"- public_analyst_signal.analysts_count: `{analyst.get('analysts_count') or '-'}`",
            f"- public_analyst_signal.average_target_raw: `{analyst.get('average_target_raw') or '-'}`",
            f"- public_analyst_signal.last_close_raw: `{analyst.get('last_close_raw') or '-'}`",
            f"- public_analyst_signal.spread_avg_target_pct: `{format_pct(analyst.get('spread_avg_target_pct'))}`",
            f"- public_analyst_signal.summary: {analyst.get('summary') or '-'}",
            "",
        ]
    )
    if public_transcript.get("source_rel_path"):
        lines.append(f"- public_transcript.source_ref: `{public_transcript.get('source_rel_path')}`")
    lines.extend(["",])
    if analyst.get("source_rel_path"):
        lines.append(f"- public_analyst_signal.source_ref: `{analyst.get('source_rel_path')}`")
    lines.append("")
    card_path.write_text("\n".join(lines), encoding="utf-8")
    return card_path


def write_batch_summary(summary_path, created_at, batch_date, focus_strategy, source_rel_path, items):
    priority_counts = Counter(item["priority"]["label"] for item in items)
    lines = [
        "# SMR 标的策略观察卡批次",
        "",
        f"- created_at: {created_at}",
        f"- batch_date: {batch_date}",
        f"- focus_strategy: {focus_strategy}",
        f"- item_count: {len(items)}",
        f"- priority_counts: {dict(priority_counts)}",
        f"- source_objective_monitor_rel_path: {source_rel_path}",
        "",
        "## 当前优先盯盘标的",
        "",
    ]

    if not items:
        lines.append("- 当前没有可生成的策略观察卡。")
    else:
        for item in items[:5]:
            lines.extend(
                [
                    f"### {item['name']} / {item['ts_code']}",
                    "",
                    f"- priority: {display_label(item['priority']['label'])} / score=`{item['priority']['score']}`",
                    f"- objective_view: {display_label(item.get('objective_view'))}",
                    f"- trend_state: {display_label(item['trend_state']['label'])} / {item['trend_state']['summary']}",
                    f"- valuation_pressure: {display_label(item['valuation_pressure']['label'])} / {item['valuation_pressure']['summary']}",
                    f"- research_staleness: {display_label(item['research_staleness']['label'])} / {item['research_staleness']['summary']}",
                    f"- capital_flow: {item.get('capital_flow_summary') or '-'}",
                    f"- events: {item.get('event_summary') or '-'}",
                    f"- official_material: {display_label((item.get('official_material') or {}).get('freshness_label'))} / {((item.get('official_material') or {}).get('summary') or '-')}",
                    f"- public_transcript: {display_label((item.get('public_transcript') or {}).get('freshness_label'))} / {((item.get('public_transcript') or {}).get('summary') or '-')}",
                    f"- public_analyst_signal: `{public_signal_label_text((item.get('public_analyst_signal') or {}).get('stance_label'))}` / {((item.get('public_analyst_signal') or {}).get('summary') or '-')}",
                ]
            )
            if item.get("watchpoints"):
                lines.append(f"- 核心观察点：{item['watchpoints'][0]}")
            if item.get("next_check_items"):
                lines.append(f"- 下一检查项：{item['next_check_items'][0]}")
            lines.append("")

    lines.extend(["## 卡片索引", ""])
    for item in items:
        lines.append(f"- `{item['ts_code']}` -> `{item.get('card_rel_path') or ''}`")
    lines.append("")
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build strategy watch cards from objective monitor snapshot")
    parser.add_argument("--date", help="Objective monitor entity_id date, e.g. 2026-04-15")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    objective_entry = load_objective_monitor_entry(conn, entity_id=args.date)
    objective_payload = objective_entry.get("payload", {}) or {}
    relationships = objective_entry.get("relationships", {}) or {}
    batch_date = objective_entry.get("entity_id")
    focus_strategy = objective_payload.get("focus_strategy") or "unknown"
    source_rel_path = relationships.get("monitor_rel_path") or objective_payload.get("monitor_rel_path") or ""
    raw_items = objective_payload.get("items") or []

    output_dir = OUTPUT_ROOT / batch_date
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "00_strategy_watch_batch.md"

    items = [
        strategy_summary_item(
            conn,
            item,
            official_material=summarize_official_materials(conn, item.get("ts_code"), limit=4),
            public_analyst_signal=summarize_public_analyst_signal(conn, item.get("ts_code")),
            public_transcript=latest_public_transcript_snapshot(conn, item.get("ts_code")),
        )
        for item in raw_items
    ]
    items = sorted(items, key=summary_sort_key)
    for item in items:
        card_path = write_card(output_dir, created_at, batch_date, source_rel_path, item)
        item["card_rel_path"] = relative_to_project(card_path)
    write_batch_summary(summary_path, created_at, batch_date, focus_strategy, source_rel_path, items)

    priority_counts = Counter(item["priority"]["label"] for item in items)
    entry = register_snapshot(
        conn,
        entity_type="strategy_watch_batch",
        entity_id=batch_date,
        status="generated" if items else "empty",
        source="build_strategy_watch_cards.py",
        relationships={
            "summary_rel_path": relative_to_project(summary_path),
            "objective_monitor_rel_path": source_rel_path,
            "objective_monitor_entry_id": objective_entry["id"],
        },
        payload={
            "focus_strategy": focus_strategy,
            "item_count": len(items),
            "priority_counts": dict(priority_counts),
            "summary_rel_path": relative_to_project(summary_path),
            "card_rel_paths": [item.get("card_rel_path") for item in items],
            "top_focus_items": items[:3],
            "items": items,
        },
        created_at=created_at,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="标的策略观察卡批次已更新，自动转交 Hermes-like 研究代理补充解释并同步调度。",
        created_by="build_strategy_watch_cards.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "build_strategy_watch_cards.py",
        "success",
        "strategy watch cards built",
        {
            "entity_id": batch_date,
            "focus_strategy": focus_strategy,
            "item_count": len(items),
            "summary_rel_path": relative_to_project(summary_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Strategy watch batch registered: {batch_date}")
    print(f"Summary file: {summary_path}")
    print(f"Card count: {len(items)}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
