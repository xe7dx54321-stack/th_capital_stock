#!/usr/bin/env python3
"""Build a theme-based deep market analysis snapshot for opportunity discovery."""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_research import latest_external_research_snapshot
from smr_data_health import check_freshness_gate, gate_to_dict
from smr_decision import record_agent_run
from smr_official_materials import summarize_official_materials
from smr_paths import env_or_project_path, relative_to_project
from smr_public_analyst_digest import summarize_public_analyst_signal
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map, ordered_unique, parse_deep_analysis_theme_registry, relation_exists, split_ts_code

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_DEEP_ANALYSIS_DIR", "02_research", "deep_analysis")
SCRIPT_NAME = "build_deep_market_analysis_snapshot.py"

POOL_PRIORITY = {
    "recommended": 0,
    "candidate": 1,
    "watchlist": 2,
    "portfolio_seed": 3,
    "seed": 4,
    "us_benchmark": 5,
}

THEME_DISPLAY = {
    "ai": "人工智能",
    "photonics": "光通信",
    "new_energy": "新能源",
    "scale_up": "Scale Up",
    "scale_out": "Scale Out",
}

SCORE_BUCKETS = (
    (6.8, "high_conviction", "高潜在低估"),
    (5.0, "medium_conviction", "继续深挖"),
    (4.2, "watch", "观察候选"),
)

THEME_SIGNAL_BUCKETS = (
    (6.2, "strong", "值得重点深挖"),
    (4.8, "active", "继续跟踪"),
    (4.0, "watch", "保持观察"),
)


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date_prefix(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def market_from_ts_code(ts_code, fallback_market=""):
    fallback = str(fallback_market or "").strip().upper()
    if fallback:
        return fallback
    if "." not in str(ts_code or ""):
        return "US"
    _code, market = split_ts_code(ts_code)
    return market or ""


def primary_pool(pool_types):
    ordered = sorted(
        [pool for pool in ordered_unique(pool_types) if pool],
        key=lambda value: (POOL_PRIORITY.get(value, 99), value),
    )
    return ordered[0] if ordered else "none"


def load_pool_meta(conn):
    if not relation_exists(conn, "stock_pool_current"):
        return {}
    rows = conn.execute(
        """
        SELECT
            ts_code,
            MAX(sector) AS sector,
            MAX(score) AS max_score,
            GROUP_CONCAT(DISTINCT pool_type) AS pool_types
        FROM stock_pool_current
        GROUP BY ts_code
        """
    ).fetchall()
    meta = {}
    for ts_code, sector, score, pool_types in rows:
        values = ordered_unique((pool_types or "").split(","))
        meta[ts_code] = {
            "sector": sector,
            "score": safe_float(score),
            "pool_types": values,
            "primary_pool": primary_pool(values),
        }
    return meta


def load_price_window(conn, ts_code, market, limit=120):
    if market == "US":
        rows = conn.execute(
            """
            SELECT trade_date, close, pct_chg
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ts_code, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT trade_date, close, pct_chg
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ts_code, limit),
        ).fetchall()
    return [
        {
            "trade_date": row[0],
            "close": safe_float(row[1]),
            "pct_chg": safe_float(row[2]),
        }
        for row in rows
    ]


def moving_average(window, length):
    closes = [safe_float(item.get("close")) for item in window[:length]]
    closes = [value for value in closes if value is not None]
    if len(closes) < length:
        return None
    return round(sum(closes) / len(closes), 4)


def period_return(window, offset):
    if len(window) <= offset:
        return None
    latest = safe_float(window[0].get("close"))
    anchor = safe_float(window[offset].get("close"))
    if latest in (None, 0) or anchor in (None, 0):
        return None
    return round((latest - anchor) / anchor * 100, 2)


def load_latest_factor_snapshot(conn, ts_code):
    if not relation_exists(conn, "factor_daily"):
        return {"trade_date": None, "factors": {}}
    trade_date_row = conn.execute(
        """
        SELECT trade_date
        FROM factor_daily
        WHERE ts_code=?
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not trade_date_row:
        return {"trade_date": None, "factors": {}}
    trade_date = trade_date_row[0]
    rows = conn.execute(
        """
        SELECT factor_name, factor_value
        FROM factor_daily
        WHERE ts_code=? AND trade_date=?
        ORDER BY factor_name
        """,
        (ts_code, trade_date),
    ).fetchall()
    return {
        "trade_date": trade_date,
        "factors": {factor_name: safe_float(factor_value) for factor_name, factor_value in rows},
    }


def recent_event_count(conn, ts_code, days=21):
    if not relation_exists(conn, "market_event"):
        return 0
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM market_event
        WHERE entity_id=?
          AND datetime(COALESCE(publish_time, created_at)) >= datetime(?)
        """,
        (ts_code, cutoff),
    ).fetchone()
    return int((row or [0])[0] or 0)


def source_count(conn, ts_code):
    if not relation_exists(conn, "source_manifest"):
        return 0
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM source_manifest
        WHERE status='active'
          AND entity_id=?
        """,
        (ts_code,),
    ).fetchone()
    return int((row or [0])[0] or 0)


def calc_target_gap_pct(close_price, market, research_snapshot):
    if market not in {"SZ", "SH", "BJ"}:
        return None
    target_price = safe_float((research_snapshot or {}).get("target_price_yuan"))
    if target_price in (None, 0) or close_price in (None, 0):
        return None
    return round((target_price - close_price) / close_price * 100, 2)


def price_trend_label(close_price, ma20, ma60):
    if close_price is None or ma20 is None or ma60 is None:
        return "mixed", "价格结构数据还不完整，当前先保留观察。"
    if close_price >= ma20 >= ma60:
        return "trend_strong", "价格站在 20/60 日均线之上，结构仍偏顺。"
    if close_price >= ma20 and ma20 >= ma60 * 0.98:
        return "trend_positive", "价格站在短期均线之上，趋势还算偏正。"
    if close_price < ma20 < ma60:
        return "trend_weak", "价格落在短中期均线下方，先看修复。"
    return "mixed", "价格结构还在来回拉扯，暂时不算完全顺。"


def score_bucket(score, buckets):
    for threshold, value, label in buckets:
        if score >= threshold:
            return value, label
    return "low", "暂不优先"


def freshness_bonus(label):
    return {
        "fresh_hot": 1.0,
        "fresh": 0.8,
        "usable": 0.4,
        "stale": -0.2,
        "missing": -0.4,
    }.get(str(label or "").strip(), 0.0)


def transcript_bonus(label):
    return {
        "fresh": 0.7,
        "usable": 0.4,
        "stale": -0.2,
        "missing": -0.4,
    }.get(str(label or "").strip(), 0.0)


def public_signal_bonus(stance_label):
    return {
        "supportive_strong": 1.0,
        "supportive": 0.7,
        "neutral_watch": 0.3,
        "neutral": 0.0,
        "stretched": -0.6,
        "cautious": -1.0,
        "missing": -0.2,
        "not_applicable": 0.0,
    }.get(str(stance_label or "").strip(), 0.0)


def score_candidate(item):
    score = 0.0
    reasons = []
    risks = []

    pool = item.get("primary_pool")
    score += {
        "recommended": 1.2,
        "candidate": 0.9,
        "watchlist": 0.4,
        "portfolio_seed": 0.4,
        "seed": 0.2,
        "us_benchmark": 0.3,
    }.get(pool, 0.0)

    trend_label = item.get("trend_label")
    score += {
        "trend_strong": 1.2,
        "trend_positive": 0.8,
        "mixed": 0.2,
        "trend_weak": -0.8,
    }.get(trend_label, 0.0)
    if trend_label == "trend_strong":
        reasons.append("价格结构仍然顺，短中期均线没有破坏。")
    elif trend_label == "trend_weak":
        risks.append("价格还没修好，先别把结构性反弹当成趋势。")

    pe_ttm = safe_float(item.get("pe_ttm"))
    pb = safe_float(item.get("pb"))
    revenue_yoy = safe_float(item.get("revenue_yoy"))
    net_profit_yoy = safe_float(item.get("net_profit_yoy"))
    rsi_14 = safe_float(item.get("rsi_14"))
    return_20d = safe_float(item.get("return_20d"))
    return_60d = safe_float(item.get("return_60d"))

    if pe_ttm is not None:
        if pe_ttm <= 25:
            score += 1.6
            reasons.append(f"PE(TTM) 约 {pe_ttm:.1f}，估值压力还不算高。")
        elif pe_ttm <= 45:
            score += 1.0
            reasons.append(f"PE(TTM) 约 {pe_ttm:.1f}，估值没有过度透支。")
        elif pe_ttm <= 70:
            score += 0.4
        elif pe_ttm > 100:
            score -= 1.4
            risks.append(f"PE(TTM) 已到 {pe_ttm:.1f}，兑现一旦跟不上回撤会放大。")
        else:
            score -= 0.8

    if pb is not None:
        if pb <= 4:
            score += 0.8
        elif pb <= 7:
            score += 0.4
        elif pb > 10:
            score -= 0.8
            risks.append(f"PB 已到 {pb:.1f}，资产端估值也不便宜。")

    if revenue_yoy is not None:
        if revenue_yoy >= 40:
            score += 1.0
            reasons.append(f"营收同比约 {revenue_yoy:.1f}%，增长还在兑现。")
        elif revenue_yoy >= 20:
            score += 0.7
            reasons.append(f"营收同比约 {revenue_yoy:.1f}%，基本面不是空心的。")
        elif revenue_yoy < 0:
            score -= 0.8
            risks.append(f"营收同比约 {revenue_yoy:.1f}%，收入端还没修好。")

    if net_profit_yoy is not None:
        if net_profit_yoy >= 40:
            score += 1.2
            reasons.append(f"净利润同比约 {net_profit_yoy:.1f}%，利润释放速度较快。")
        elif net_profit_yoy >= 20:
            score += 0.8
        elif net_profit_yoy < 0:
            score -= 0.9
            risks.append(f"净利润同比约 {net_profit_yoy:.1f}%，盈利修复还没确认。")

    target_gap_pct = safe_float(item.get("target_gap_pct"))
    if target_gap_pct is not None:
        if target_gap_pct >= 30:
            score += 2.0
            reasons.append("外部研究关注度较高，卖方观点方向偏正面。")
        elif target_gap_pct >= 15:
            score += 1.4
            reasons.append("外部卖方观点偏积极，值得跟踪验证。")
        elif target_gap_pct >= 5:
            score += 0.7
        elif target_gap_pct < 0:
            score -= 1.0
            risks.append("外部预期已被市场充分反映，需关注基本面驱动。")

    analyst_gap_pct = safe_float(item.get("analyst_gap_pct"))
    if analyst_gap_pct is not None:
        if analyst_gap_pct >= 25:
            score += 2.2
            reasons.append("外部卖方一致预期方向偏正面，关注度提升。")
        elif analyst_gap_pct >= 10:
            score += 1.4
            reasons.append("外部预期方向积极，建议结合基本面变化跟踪。")
        elif analyst_gap_pct >= 0:
            score += 0.6
        else:
            score -= 1.2
            risks.append("外部预期分歧不大，需寻找新的预期差驱动。")

    public_signal = item.get("public_signal") or {}
    stance_label = public_signal.get("stance_label")
    score += public_signal_bonus(stance_label)
    if stance_label in {"supportive", "supportive_strong"}:
        reasons.append("公开卖方口径仍偏积极，不是明显的一致性反向信号。")
    elif stance_label in {"stretched", "cautious"}:
        risks.append("公开卖方口径偏保守，市场预期可能已经走得过满。")

    official_material = item.get("official_material") or {}
    transcript = item.get("public_transcript") or {}
    official_label = official_material.get("freshness_label")
    transcript_label = transcript.get("freshness_label")
    score += freshness_bonus(official_label)
    score += transcript_bonus(transcript_label)
    if official_label in {"fresh_hot", "fresh"}:
        reasons.append("最近仍有较新的一手材料，判断不完全靠旧研报。")
    elif official_label in {"stale", "missing"}:
        risks.append("一手材料偏旧，后续要防信息滞后。")
    if transcript_label in {"fresh", "usable"}:
        reasons.append("还能直接复核管理层原话，研究底座更扎实。")

    event_count = int(item.get("event_count_21d") or 0)
    if event_count >= 4:
        score += 0.5
        reasons.append("近三周事件密度较高，主题关注度仍在。")
    elif event_count >= 2:
        score += 0.3
    elif event_count == 0:
        score -= 0.2
        risks.append("近端缺少明确催化，推进节奏可能偏慢。")

    source_cnt = int(item.get("source_count") or 0)
    if source_cnt >= 12:
        score += 0.4
    elif source_cnt >= 6:
        score += 0.2

    if rsi_14 is not None and rsi_14 >= 75:
        score -= 0.8
        risks.append(f"RSI14 约 {rsi_14:.1f}，短线偏热。")
    if return_20d is not None:
        if return_20d > 25:
            score -= 0.8
            risks.append(f"近 20 个交易日涨幅约 {return_20d:.1f}%，追高性价比下降。")
        elif return_20d > 15:
            score -= 0.4
    if return_60d is not None and return_60d > 45:
        score -= 0.5

    reasons = ordered_unique(reasons)
    risks = ordered_unique(risks)
    if not reasons:
        reasons = ["当前更多是结构和信息覆盖层面的观察机会，后续还需要更强催化来确认。"]
    if not risks:
        risks = ["当前没有特别突出的结构性风险，但仍需继续跟踪新催化和兑现速度。"]
    return round(score, 2), reasons[:6], risks[:5]


def build_source_paths(item):
    paths = []
    research = item.get("external_research") or {}
    public_signal = item.get("public_signal") or {}
    official_material = item.get("official_material") or {}
    public_transcript = item.get("public_transcript") or {}
    for value in (
        research.get("source_rel_path"),
        public_signal.get("source_rel_path"),
        public_transcript.get("source_rel_path"),
        *(official_material.get("source_rel_paths") or [])[:3],
    ):
        if value:
            paths.append(value)
    return ordered_unique(paths)


def build_candidate_summary(item):
    lead = "、".join(item.get("theme_labels") or [])
    reasons = item.get("why") or []
    if len(reasons) >= 2:
        return f"{lead}方向里，这只票当前最主要的支撑是：{reasons[0]} {reasons[1]}"
    if reasons:
        return f"{lead}方向里，这只票当前最主要的支撑是：{reasons[0]}"
    return f"{lead}方向里，这只票目前先保持客观观察。"


def theme_summary(theme_meta, items):
    if not items:
        return {
            "theme": theme_meta["theme"],
            "label": theme_meta["label"],
            "priority": theme_meta["priority"],
            "description": theme_meta.get("description"),
            "signal": "watch",
            "signal_label": "保持观察",
            "target_count": 0,
            "candidate_count": 0,
            "markets": {},
            "leaders": [],
            "summary": "当前没有拿到足够结果。",
        }

    ordered_items = sorted(
        items,
        key=lambda row: (-(safe_float(row.get("undervaluation_score")) or 0.0), row.get("ts_code") or ""),
    )
    leader_items = ordered_items[:3]
    candidate_count = sum(1 for row in ordered_items if row.get("bucket") in {"high_conviction", "medium_conviction", "watch"})
    avg_top_score = round(
        sum(safe_float(row.get("undervaluation_score")) or 0.0 for row in leader_items) / max(len(leader_items), 1),
        2,
    )
    signal, signal_label = score_bucket(avg_top_score, THEME_SIGNAL_BUCKETS)
    markets = Counter(row.get("market") or "-" for row in ordered_items)
    leaders_text = "、".join(f"{row.get('name')}({row.get('ts_code')})" for row in leader_items)
    summary = f"{theme_meta['label']}当前更值得优先看 {leaders_text}，说明这一主题仍有继续深挖价值。"
    return {
        "theme": theme_meta["theme"],
        "label": theme_meta["label"],
        "priority": theme_meta["priority"],
        "description": theme_meta.get("description"),
        "signal": signal,
        "signal_label": signal_label,
        "target_count": len(ordered_items),
        "candidate_count": candidate_count,
        "avg_top_score": avg_top_score,
        "markets": dict(markets),
        "leaders": [
            {
                "ts_code": row.get("ts_code"),
                "name": row.get("name"),
                "market": row.get("market"),
                "score": row.get("undervaluation_score"),
            }
            for row in leader_items
        ],
        "summary": summary,
    }


def build_overview_lines(theme_radar, a_share_candidates, us_candidates):
    lines = []
    if theme_radar:
        top_theme = sorted(theme_radar, key=lambda item: (item.get("priority", 99), -(item.get("avg_top_score") or 0.0)))[0]
        lines.append(
            f"本轮主题强度最靠前的是{top_theme.get('label')}，当前更值得优先深挖 { '、'.join(row.get('name') for row in top_theme.get('leaders')[:2]) }。"
        )
    if a_share_candidates:
        top_a = a_share_candidates[0]
        lines.append(f"A股侧当前最值得继续深挖的是 {top_a.get('name')}，核心原因是 {top_a.get('why')[0]}")
    if us_candidates:
        top_us = us_candidates[0]
        lines.append(f"美股侧当前最值得继续深挖的是 {top_us.get('name')}，核心原因是 {top_us.get('why')[0]}")
    return lines[:3]


def format_pct(value):
    value = safe_float(value)
    if value is None:
        return "-"
    return f"{value:+.2f}%"


def format_number(value):
    value = safe_float(value)
    if value is None:
        return "-"
    return f"{value:,.2f}"


def write_markdown(path, payload):
    lines = [
        "# 全网信息深度分析快照",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- batch_date: {payload['batch_date']}",
        f"- cadence_hours: {payload['cadence_hours']}",
        f"- theme_count: {payload['theme_count']}",
        f"- a_share_candidate_count: {payload['a_share_candidate_count']}",
        f"- us_candidate_count: {payload['us_candidate_count']}",
        "",
        "## 本轮结论",
        "",
    ]
    for line in payload.get("overview_lines") or ["当前还没有形成可读结论。"]:
        lines.append(f"- {line}")

    lines.extend(
        [
            "",
            "## 主题雷达",
            "",
            "| 主题 | 当前状态 | 覆盖标的 | 候选数量 | 代表标的 | 观察结论 |",
            "|------|----------|----------|----------|----------|----------|",
        ]
    )
    for item in payload.get("theme_radar") or []:
        leaders = "、".join(f"{row['name']}({row['ts_code']})" for row in (item.get("leaders") or [])[:3]) or "-"
        lines.append(
            f"| {item.get('label')} | {item.get('signal_label')} | {item.get('target_count')} | {item.get('candidate_count')} | {leaders} | {item.get('summary') or '-'} |"
        )

    def write_candidate_block(title, items):
        lines.extend(["", f"## {title}", ""])
        if not items:
            lines.append("- 当前没有形成可读候选。")
            return
        for index, item in enumerate(items, start=1):
            lines.extend(
                [
                    f"### {index}. {item.get('name')} ({item.get('ts_code')})",
                    "",
                    f"- 主题: {' / '.join(item.get('theme_labels') or ['-'])}",
                    f"- 机会分: {item.get('undervaluation_score')} / {item.get('bucket_label')}",
                    f"- 当前价格: {format_number(item.get('latest_close'))} / 日涨跌 {format_pct(item.get('latest_pct_chg'))} / 交易日 {item.get('latest_trade_date') or '-'}",
                    f"- 当前判断: {item.get('summary')}",
                    f"- 趋势结构: {item.get('trend_summary')}",
                    f"- 估值与增长: PE(TTM) {format_number(item.get('pe_ttm'))} / PB {format_number(item.get('pb'))} / 营收同比 {format_pct(item.get('revenue_yoy'))} / 净利润同比 {format_pct(item.get('net_profit_yoy'))}",
                    f"- 外部观点倾向: {format_pct(item.get('target_gap_pct'))}",
                    f"- 卖方预期方向: {format_pct(item.get('analyst_gap_pct'))}",
                    f"- 最近三周事件数: {item.get('event_count_21d') or 0}",
                    "- 为什么值得继续看:",
                ]
            )
            for reason in item.get("why") or ["当前没有提取到明确理由。"]:
                lines.append(f"  - {reason}")
            lines.append("- 主要风险:")
            for risk in item.get("risks") or ["当前没有提取到明确风险。"]:
                lines.append(f"  - {risk}")
            lines.append("- 原文入口:")
            source_paths = item.get("source_rel_paths") or []
            if source_paths:
                for rel_path in source_paths:
                    lines.append(f"  - {rel_path}")
            else:
                lines.append("  - 当前没有可点击原文入口。")
            lines.append("")

    write_candidate_block("A股低估候选", payload.get("a_share_candidates") or [])
    write_candidate_block("美股低估候选", payload.get("us_candidates") or [])

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_candidate_item(conn, row, theme_map, pool_meta, name_map):
    ts_code = row["ts_code"]
    market = market_from_ts_code(ts_code, row.get("market"))
    price_window = load_price_window(conn, ts_code, market, limit=120)
    if not price_window:
        return None

    latest_price = price_window[0]
    latest_close = safe_float(latest_price.get("close"))
    factor_snapshot = load_latest_factor_snapshot(conn, ts_code)
    factors = factor_snapshot.get("factors") or {}
    ma20 = safe_float(factors.get("ma_20")) or moving_average(price_window, 20)
    ma60 = safe_float(factors.get("ma_60")) or moving_average(price_window, 60)
    ma120 = safe_float(factors.get("ma_120")) or moving_average(price_window, 120)
    trend_label, trend_summary = price_trend_label(latest_close, ma20, ma60)
    external_research = latest_external_research_snapshot(conn, ts_code) or {}
    public_signal = summarize_public_analyst_signal(conn, ts_code) or {}
    official_material = summarize_official_materials(conn, ts_code, limit=4) or {}
    public_transcript = latest_public_transcript_snapshot(conn, ts_code) or {}
    target_gap_pct = calc_target_gap_pct(latest_close, market, external_research)
    analyst_gap_pct = safe_float(public_signal.get("spread_avg_target_pct"))

    pool_row = pool_meta.get(ts_code) or {}
    theme_labels = [theme_map.get(theme_id, {}).get("label", THEME_DISPLAY.get(theme_id, theme_id)) for theme_id in row.get("themes") or []]

    item = {
        "ts_code": ts_code,
        "name": row.get("name") or name_map.get(ts_code, ts_code),
        "market": market,
        "sector": pool_row.get("sector") or row.get("sector"),
        "pool_types": pool_row.get("pool_types") or [],
        "primary_pool": pool_row.get("primary_pool") or "none",
        "pool_score": pool_row.get("score"),
        "theme_ids": row.get("themes") or [],
        "theme_labels": theme_labels,
        "role": row.get("role"),
        "notes": row.get("notes"),
        "latest_trade_date": latest_price.get("trade_date"),
        "latest_close": latest_close,
        "latest_pct_chg": safe_float(latest_price.get("pct_chg")),
        "ma_20": ma20,
        "ma_60": ma60,
        "ma_120": ma120,
        "return_20d": period_return(price_window, 20),
        "return_60d": period_return(price_window, 60),
        "trend_label": trend_label,
        "trend_summary": trend_summary,
        "rsi_14": safe_float(factors.get("rsi_14")),
        "pe_ttm": safe_float(factors.get("pe_ttm")),
        "pb": safe_float(factors.get("pb")),
        "revenue_yoy": safe_float(factors.get("revenue_yoy")),
        "net_profit_yoy": safe_float(factors.get("net_profit_yoy")),
        "external_research": external_research,
        "public_signal": public_signal,
        "official_material": official_material,
        "public_transcript": public_transcript,
        "target_gap_pct": target_gap_pct,
        "analyst_gap_pct": analyst_gap_pct,
        "event_count_21d": recent_event_count(conn, ts_code, days=21),
        "source_count": source_count(conn, ts_code),
    }
    score, reasons, risks = score_candidate(item)
    bucket, bucket_display = score_bucket(score, SCORE_BUCKETS)
    item["undervaluation_score"] = score
    item["bucket"] = bucket
    item["bucket_label"] = bucket_display
    item["why"] = reasons
    item["risks"] = risks
    item["summary"] = build_candidate_summary({**item, "why": reasons})
    item["source_rel_paths"] = build_source_paths(item)
    return item


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        freshness_gate = check_freshness_gate(
            conn,
            module_name="deep_market_scan",
            required_data_types=["news", "filings", "fundamentals"],
            allow_degraded=True,
        )
        theme_registry = parse_deep_analysis_theme_registry()
        theme_map = theme_registry.get("themes") or {}
        target_rows = theme_registry.get("targets") or []
        pool_meta = load_pool_meta(conn)
        name_map = combined_name_map(conn)

        coverage_gaps = []
        all_items = []
        for row in target_rows:
            item = build_candidate_item(conn, row, theme_map, pool_meta, name_map)
            if item is None:
                coverage_gaps.append(
                    {
                        "ts_code": row.get("ts_code"),
                        "name": row.get("name"),
                        "themes": row.get("themes") or [],
                        "reason": "missing_price_window",
                    }
                )
                continue
            all_items.append(item)

        all_items.sort(key=lambda row: (-(safe_float(row.get("undervaluation_score")) or 0.0), row.get("ts_code") or ""))
        theme_items = {theme_id: [] for theme_id in theme_map}
        for item in all_items:
            for theme_id in item.get("theme_ids") or []:
                if theme_id in theme_items:
                    theme_items[theme_id].append(item)

        theme_radar = [
            theme_summary(theme_map[theme_id], theme_items.get(theme_id) or [])
            for theme_id in sorted(theme_map, key=lambda key: (theme_map[key].get("priority", 99), key))
        ]

        a_share_candidates = [
            item
            for item in all_items
            if item.get("market") in {"SZ", "SH", "BJ"} and item.get("bucket") in {"high_conviction", "medium_conviction", "watch"}
        ][:8]
        us_candidates = [
            item
            for item in all_items
            if item.get("market") == "US" and item.get("bucket") in {"high_conviction", "medium_conviction", "watch"}
        ][:8]

        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "cadence_hours": min((item.get("cadence_hours") or 12) for item in theme_map.values()) if theme_map else 12,
            "theme_count": len(theme_map),
            "target_count": len(target_rows),
            "evaluated_count": len(all_items),
            "a_share_candidate_count": len(a_share_candidates),
            "us_candidate_count": len(us_candidates),
            "overview_lines": build_overview_lines(theme_radar, a_share_candidates, us_candidates),
            "theme_radar": theme_radar,
            "a_share_candidates": a_share_candidates,
            "us_candidates": us_candidates,
            "coverage_gaps": coverage_gaps[:10],
            "freshness_gate_result": gate_to_dict(freshness_gate),
            "data_health_snapshot": freshness_gate.data_health_snapshot,
        }

        output_path = OUTPUT_DIR / f"{generated_at[:10]}_{generated_at[11:13]}{generated_at[14:16]}{generated_at[17:19]}_deep_market_analysis.md"
        write_markdown(output_path, payload)

        registry_entry = register_snapshot(
            conn,
            entity_type="deep_market_analysis_snapshot",
            entity_id=batch_date,
            status="generated" if (a_share_candidates or us_candidates) else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
                "theme_registry_rel_path": "00_control/deep_analysis_theme_registry.md",
            },
            payload={
                **payload,
                "summary_rel_path": relative_to_project(output_path),
            },
            created_at=generated_at,
        )
        record_agent_run(
            conn,
            agent_or_script=SCRIPT_NAME,
            status="success",
            entity_type="deep_market_analysis_snapshot",
            entity_id=batch_date,
            data_health_snapshot=freshness_gate.data_health_snapshot,
            freshness_gate_result=gate_to_dict(freshness_gate),
            output_status=registry_entry["status"],
            block_reasons=freshness_gate.reasons if freshness_gate.status == "block" else [],
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "deep market analysis snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "target_count": payload["target_count"],
            "evaluated_count": payload["evaluated_count"],
            "a_share_candidate_count": payload["a_share_candidate_count"],
            "us_candidate_count": payload["us_candidate_count"],
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    print(f"Deep market analysis snapshot: {relative_to_project(output_path)}")
    print(f"A-share candidates: {payload['a_share_candidate_count']}")
    print(f"US candidates: {payload['us_candidate_count']}")


if __name__ == "__main__":
    main()
