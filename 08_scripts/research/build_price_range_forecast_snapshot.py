#!/usr/bin/env python3
"""Build short-horizon price-range forecasts for active covered equities and proxy baskets."""

from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map, ordered_unique

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path(
    "SMR_PRICE_RANGE_FORECAST_DIR",
    "06_reports",
    "adhoc",
    "price_range_forecast",
)
SCRIPT_NAME = "build_price_range_forecast_snapshot.py"

POOL_PRIORITY = {
    "recommended": 0,
    "candidate": 1,
    "watchlist": 2,
    "portfolio_seed": 3,
    "seed": 4,
    "us_benchmark": 5,
}

MARKET_LABELS = {
    "A": "A股",
    "H": "港股",
    "US": "美股",
}

INDEX_PROXY_SPECS = (
    {
        "proxy_id": "a_coverage_basket",
        "name": "A股覆盖篮子指数代理",
        "market": "A",
        "description": "基于当前系统活跃 A股覆盖池做的等权方向代理，不代表上证指数、沪深300或中证1000。",
    },
    {
        "proxy_id": "hk_coverage_basket",
        "name": "港股覆盖篮子指数代理",
        "market": "H",
        "description": "基于当前系统活跃港股覆盖池做的等权方向代理，不代表恒生指数或恒生科技指数。",
    },
    {
        "proxy_id": "us_benchmark_basket",
        "name": "美股基准篮子指数代理",
        "market": "US",
        "description": "基于当前系统活跃美股对照池做的等权方向代理，不代表纳指、标普500或 SOX。",
    },
)


def safe_float(value):
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp(value, low, high):
    return max(low, min(high, value))


def mean(values):
    data = [safe_float(value) for value in values if safe_float(value) is not None]
    if not data:
        return None
    return sum(data) / len(data)


def sample_std(values):
    data = [safe_float(value) for value in values if safe_float(value) is not None]
    if len(data) < 2:
        return None
    avg = sum(data) / len(data)
    variance = sum((value - avg) ** 2 for value in data) / (len(data) - 1)
    return math.sqrt(max(variance, 0.0))


def compact_text(value, limit=88):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def market_from_symbol(ts_code):
    code = str(ts_code or "").strip().upper()
    if not code:
        return ""
    if "." not in code:
        return "US"
    if code.endswith(".HK"):
        return "H"
    return "A"


def market_label(market):
    return MARKET_LABELS.get(str(market or "").upper(), str(market or "-"))


def primary_pool(pool_types):
    ordered = sorted(ordered_unique(pool_types or []), key=lambda value: (POOL_PRIORITY.get(value, 99), value))
    return ordered[0] if ordered else "none"


def confidence_label(score):
    number = safe_float(score) or 0.0
    if number >= 0.72:
        return "高"
    if number >= 0.58:
        return "中"
    return "低"


def latest_pct_change(rows):
    if not rows:
        return None
    direct = safe_float(rows[0].get("pct_chg"))
    if direct is not None:
        return direct / 100.0
    latest_close = safe_float(rows[0].get("close"))
    prev_close = safe_float(rows[1].get("close")) if len(rows) > 1 else None
    if latest_close in (None, 0) or prev_close in (None, 0):
        return None
    return latest_close / prev_close - 1.0


def latest_trade_date(items):
    dates = [str(item.get("latest_trade_date") or "").strip() for item in items or [] if item.get("latest_trade_date")]
    if not dates:
        return None
    return max(dates)


def load_active_pool_meta(conn):
    rows = conn.execute(
        """
        SELECT
            ts_code,
            MAX(sector) AS sector,
            GROUP_CONCAT(DISTINCT pool_type) AS pool_types
        FROM stock_pool_current
        WHERE status='active'
        GROUP BY ts_code
        ORDER BY ts_code
        """
    ).fetchall()
    meta = {}
    for ts_code, sector, pool_types in rows:
        pools = ordered_unique((pool_types or "").split(","))
        meta[ts_code] = {
            "sector": sector,
            "pool_types": pools,
            "primary_pool": primary_pool(pools),
            "market": market_from_symbol(ts_code),
        }
    return meta


def load_price_window(conn, symbol, market, limit=80):
    if market == "US":
        rows = conn.execute(
            """
            SELECT trade_date, open, close, high, low, vol, amount, pct_chg
            FROM us_daily_bar
            WHERE symbol=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT trade_date, open, close, high, low, vol, amount, pct_chg
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()
    return [
        {
            "trade_date": row[0],
            "open": safe_float(row[1]),
            "close": safe_float(row[2]),
            "high": safe_float(row[3]),
            "low": safe_float(row[4]),
            "vol": safe_float(row[5]),
            "amount": safe_float(row[6]),
            "pct_chg": safe_float(row[7]),
        }
        for row in rows
    ]


def load_latest_factor_map(conn, ts_code):
    row = conn.execute(
        """
        SELECT MAX(trade_date)
        FROM factor_daily
        WHERE ts_code=?
        """,
        (ts_code,),
    ).fetchone()
    trade_date = row[0] if row else None
    if not trade_date:
        return {}
    rows = conn.execute(
        """
        SELECT factor_name, factor_value
        FROM factor_daily
        WHERE ts_code=? AND trade_date=?
        ORDER BY factor_name
        """,
        (ts_code, trade_date),
    ).fetchall()
    return {factor_name: safe_float(factor_value) for factor_name, factor_value in rows}


def latest_market_event_summary(conn, ts_code):
    row = conn.execute(
        """
        SELECT title, event_type, publish_time, event_date, source_rel_path
        FROM market_event_latest
        WHERE entity_type='stock' AND entity_id=?
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return {
            "headline": "当前还没有在事件库里拿到足够新的公开资讯。",
            "published_at": None,
            "event_type": None,
            "source_rel_path": None,
        }
    title = str(row[0] or "").strip() or "最新事件"
    event_type = str(row[1] or "").strip() or None
    published_at = row[2] or row[3]
    headline = title if not event_type else f"{title}。来源类型：{event_type}。"
    return {
        "headline": headline,
        "published_at": published_at,
        "event_type": event_type,
        "source_rel_path": row[4],
    }


def average_close(rows, length):
    closes = [safe_float(row.get("close")) for row in rows[:length]]
    closes = [value for value in closes if value is not None]
    if len(closes) < length:
        return None
    return sum(closes) / len(closes)


def forecast_from_rows(rows, factors=None, market="A"):
    rows = rows or []
    factors = factors or {}
    if len(rows) < 15:
        return None

    closes_desc = [safe_float(row.get("close")) for row in rows if safe_float(row.get("close")) is not None]
    if len(closes_desc) < 15:
        return None
    closes_asc = list(reversed(closes_desc))
    latest_close = closes_desc[0]
    prev_close = closes_desc[1] if len(closes_desc) > 1 else None
    latest_change = latest_pct_change(rows) or 0.0

    recent_returns = []
    for index in range(1, len(closes_asc)):
        base = closes_asc[index - 1]
        current = closes_asc[index]
        if base in (None, 0) or current is None:
            continue
        recent_returns.append(current / base - 1.0)
    realized_vol = sample_std(recent_returns[-20:])
    factor_vol = safe_float(factors.get("volatility_20"))
    factor_daily_vol = factor_vol / math.sqrt(252) if factor_vol is not None else None
    if realized_vol is None:
        realized_vol = factor_daily_vol
    elif factor_daily_vol is not None:
        realized_vol = (realized_vol + factor_daily_vol) / 2.0
    realized_vol = clamp(realized_vol or 0.032, 0.012, 0.08)

    ma_20 = safe_float(factors.get("ma_20"))
    ma_60 = safe_float(factors.get("ma_60"))
    ma_120 = safe_float(factors.get("ma_120"))
    if ma_20 is None:
        ma_20 = average_close(rows, 20)
    if ma_60 is None:
        ma_60 = average_close(rows, 60)
    if ma_120 is None:
        ma_120 = average_close(rows, 120)

    return_5d = latest_close / closes_desc[5] - 1.0 if len(closes_desc) > 5 and closes_desc[5] not in (None, 0) else None
    return_20d = latest_close / closes_desc[20] - 1.0 if len(closes_desc) > 20 and closes_desc[20] not in (None, 0) else None

    trend_strength = safe_float(factors.get("trend_strength"))
    rsi_14 = safe_float(factors.get("rsi_14"))
    macd_hist = safe_float(factors.get("macd_hist"))

    drift_score = 0.0
    driver_lines = []

    if return_5d is not None:
        drift_score += clamp(return_5d / 0.10, -1.3, 1.3) * 0.34
        driver_lines.append(f"近5日变化 {return_5d * 100:+.2f}%")
    if return_20d is not None:
        drift_score += clamp(return_20d / 0.22, -1.3, 1.3) * 0.24
        driver_lines.append(f"近20日变化 {return_20d * 100:+.2f}%")
    if trend_strength is not None:
        drift_score += clamp(trend_strength / 3.0, -1.0, 1.0) * 0.18
        driver_lines.append(f"趋势强度 {trend_strength:.2f}")
    if ma_20 not in (None, 0):
        gap20 = latest_close / ma_20 - 1.0
        drift_score += clamp(gap20 / 0.12, -0.22, 0.22)
        driver_lines.append(f"相对 MA20 {gap20 * 100:+.2f}%")
    if ma_60 not in (None, 0):
        gap60 = latest_close / ma_60 - 1.0
        drift_score += clamp(gap60 / 0.20, -0.15, 0.15)
    if macd_hist is not None:
        macd_base = max(abs(latest_close) * 0.02, 0.8)
        drift_score += clamp(macd_hist / macd_base, -0.12, 0.12)
    if rsi_14 is not None:
        if rsi_14 >= 70:
            drift_score -= 0.10
            driver_lines.append(f"RSI14 {rsi_14:.2f} 偏热")
        elif rsi_14 <= 35:
            drift_score += 0.10
            driver_lines.append(f"RSI14 {rsi_14:.2f} 偏冷")

    if market == "US":
        drift_score *= 0.88

    next_day_bias = clamp(drift_score * 0.0085, -0.035, 0.035)
    five_day_bias = clamp(drift_score * 0.0200, -0.080, 0.080)
    sigma_1d = clamp(realized_vol, 0.012, 0.08)
    sigma_5d = clamp(realized_vol * math.sqrt(5), 0.028, 0.18)

    next_day_mid = latest_close * (1.0 + next_day_bias)
    next_day_low = latest_close * (1.0 + next_day_bias - 1.15 * sigma_1d)
    next_day_high = latest_close * (1.0 + next_day_bias + 1.15 * sigma_1d)
    five_day_mid = latest_close * (1.0 + five_day_bias)
    five_day_low = latest_close * (1.0 + five_day_bias - 1.30 * sigma_5d)
    five_day_high = latest_close * (1.0 + five_day_bias + 1.30 * sigma_5d)

    direction_score = next_day_bias / max(sigma_1d, 0.01)
    if direction_score >= 0.70:
        bias_label = "偏多"
    elif direction_score <= -0.70:
        bias_label = "偏空"
    else:
        bias_label = "中性"

    confidence = clamp(
        0.47 + min(abs(direction_score), 2.0) * 0.12 + max(0.0, 0.06 - sigma_1d) * 1.8,
        0.45,
        0.88,
    )

    next_day_width_pct = (next_day_high - next_day_low) / latest_close * 100.0 if latest_close else None
    five_day_width_pct = (five_day_high - five_day_low) / latest_close * 100.0 if latest_close else None

    return {
        "latest_close": round(latest_close, 4),
        "prev_close": round(prev_close, 4) if prev_close is not None else None,
        "latest_pct_chg": round(latest_change * 100.0, 2),
        "realized_volatility_20d": round(realized_vol * 100.0, 2),
        "bias_label": bias_label,
        "confidence": round(confidence, 2),
        "confidence_label": confidence_label(confidence),
        "next_day": {
            "low": round(next_day_low, 4),
            "mid": round(next_day_mid, 4),
            "high": round(next_day_high, 4),
            "bias_pct": round(next_day_bias * 100.0, 2),
            "range_width_pct": round(next_day_width_pct, 2) if next_day_width_pct is not None else None,
        },
        "five_day": {
            "low": round(five_day_low, 4),
            "mid": round(five_day_mid, 4),
            "high": round(five_day_high, 4),
            "bias_pct": round(five_day_bias * 100.0, 2),
            "range_width_pct": round(five_day_width_pct, 2) if five_day_width_pct is not None else None,
        },
        "ma_20": round(ma_20, 4) if ma_20 is not None else None,
        "ma_60": round(ma_60, 4) if ma_60 is not None else None,
        "ma_120": round(ma_120, 4) if ma_120 is not None else None,
        "trend_strength": trend_strength,
        "rsi_14": rsi_14,
        "driver_lines": ordered_unique(driver_lines)[:4],
    }


def summary_line(item):
    next_day = item.get("next_day") or {}
    five_day = item.get("five_day") or {}
    return (
        f"{item.get('name') or item.get('ts_code') or item.get('proxy_id')}："
        f"下一交易日大致区间 {next_day.get('low')} - {next_day.get('high')}，"
        f"5日区间 {five_day.get('low')} - {five_day.get('high')}，"
        f"方向偏置 {item.get('bias_label')}，置信度 {item.get('confidence_label')}。"
    )


def build_equity_items(conn, pool_meta):
    names = combined_name_map(conn)
    items = []
    for ts_code, meta in pool_meta.items():
        market = meta.get("market")
        rows = load_price_window(conn, ts_code, market)
        factors = load_latest_factor_map(conn, ts_code) if market != "US" else {}
        forecast = forecast_from_rows(rows, factors=factors, market=market)
        if forecast is None:
            continue
        event = latest_market_event_summary(conn, ts_code)
        item = {
            "ts_code": ts_code,
            "symbol": ts_code,
            "name": names.get(ts_code, ts_code),
            "market": market,
            "market_label": market_label(market),
            "sector": meta.get("sector"),
            "pool_types": meta.get("pool_types") or [],
            "primary_pool": meta.get("primary_pool") or "none",
            "latest_trade_date": rows[0].get("trade_date") if rows else None,
            "event_summary": event.get("headline"),
            "event_published_at": event.get("published_at"),
            "event_type": event.get("event_type"),
            "event_source_rel_path": event.get("source_rel_path"),
            **forecast,
        }
        item["summary_line"] = summary_line(item)
        items.append(item)

    items.sort(
        key=lambda item: (
            POOL_PRIORITY.get(item.get("primary_pool"), 99),
            -(abs(safe_float(((item.get("next_day") or {}).get("bias_pct"))) or 0.0)),
            -(safe_float(item.get("confidence")) or 0.0),
            item.get("ts_code") or "",
        )
    )
    return items


def build_proxy_series(conn, members, market):
    date_buckets = defaultdict(list)
    used_members = 0
    for ts_code in members:
        rows = list(reversed(load_price_window(conn, ts_code, market)))
        closes = [safe_float(row.get("close")) for row in rows if safe_float(row.get("close")) is not None]
        if len(closes) < 15:
            continue
        base_close = closes[0]
        if base_close in (None, 0):
            continue
        used_members += 1
        for row in rows:
            close = safe_float(row.get("close"))
            trade_date = row.get("trade_date")
            if close is None or trade_date in (None, ""):
                continue
            date_buckets[trade_date].append(close / base_close * 100.0)

    ordered_dates = sorted(date_buckets.keys())
    if len(ordered_dates) < 15:
        return [], used_members

    series_asc = []
    for trade_date in ordered_dates:
        proxy_close = mean(date_buckets[trade_date])
        if proxy_close is None:
            continue
        series_asc.append(
            {
                "trade_date": trade_date,
                "open": proxy_close,
                "close": proxy_close,
                "high": proxy_close,
                "low": proxy_close,
                "vol": None,
                "amount": None,
                "pct_chg": None,
            }
        )
    for index in range(1, len(series_asc)):
        prev_close = series_asc[index - 1]["close"]
        current_close = series_asc[index]["close"]
        if prev_close not in (None, 0) and current_close is not None:
            series_asc[index]["pct_chg"] = (current_close / prev_close - 1.0) * 100.0
    return list(reversed(series_asc[-80:])), used_members


def build_index_proxy_items(conn, pool_meta):
    members_by_market = defaultdict(list)
    for ts_code, meta in pool_meta.items():
        market = meta.get("market")
        if market in {"A", "H", "US"}:
            members_by_market[market].append(ts_code)

    items = []
    for spec in INDEX_PROXY_SPECS:
        members = sorted(members_by_market.get(spec["market"]) or [])
        series, used_members = build_proxy_series(conn, members, spec["market"])
        forecast = forecast_from_rows(series, factors={}, market=spec["market"])
        if forecast is None:
            continue
        item = {
            "proxy_id": spec["proxy_id"],
            "name": spec["name"],
            "market": spec["market"],
            "market_label": market_label(spec["market"]),
            "proxy_type": "coverage_proxy",
            "description": spec["description"],
            "member_count": len(members),
            "used_member_count": used_members,
            "latest_trade_date": series[0].get("trade_date") if series else None,
            "event_summary": spec["description"],
            "event_published_at": None,
            "event_type": "coverage_proxy",
            "event_source_rel_path": None,
            **forecast,
        }
        item["summary_line"] = summary_line(item)
        items.append(item)
    return items


def coverage_summary(pool_meta, equities, index_proxies):
    counts = defaultdict(int)
    for item in equities:
        counts[item.get("market")] += 1
    latest_dates = {
        "a_share_trade_date": latest_trade_date([item for item in equities if item.get("market") == "A"]),
        "hk_trade_date": latest_trade_date([item for item in equities if item.get("market") == "H"]),
        "us_trade_date": latest_trade_date([item for item in equities if item.get("market") == "US"]),
    }
    return {
        "active_symbol_count": len(pool_meta),
        "forecast_symbol_count": len(equities),
        "proxy_count": len(index_proxies),
        "a_share_count": counts.get("A", 0),
        "hk_count": counts.get("H", 0),
        "us_count": counts.get("US", 0),
        **latest_dates,
    }


def build_overview_lines(equities, index_proxies):
    lines = []
    for market in ("A", "H", "US"):
        market_items = [item for item in equities if item.get("market") == market]
        if not market_items:
            continue
        leader = sorted(
            market_items,
            key=lambda item: (
                -(abs(safe_float(((item.get("next_day") or {}).get("bias_pct"))) or 0.0)),
                -(safe_float(item.get("confidence")) or 0.0),
            ),
        )[0]
        lines.append(summary_line(leader))
    for proxy in index_proxies:
        lines.append(summary_line(proxy))
    lines.append("指数部分当前是数据库可解释的覆盖篮子方向代理，不是真实上证指数、沪深300、恒生指数或纳指行情。")
    return lines


def write_markdown(output_path, payload):
    coverage = payload.get("coverage_summary") or {}
    lines = [
        "# 个股与指数代理预测区间快照",
        "",
        f"- generated_at: {payload.get('generated_at') or '-'}",
        f"- batch_date: {payload.get('batch_date') or '-'}",
        f"- methodology: {payload.get('methodology') or '-'}",
        f"- note: {payload.get('note') or '-'}",
        (
            f"- coverage: 活跃池 {coverage.get('active_symbol_count', 0)} 只，"
            f"可预测个股 {coverage.get('forecast_symbol_count', 0)} 只，"
            f"其中 A股 {coverage.get('a_share_count', 0)} / 港股 {coverage.get('hk_count', 0)} / 美股 {coverage.get('us_count', 0)}。"
        ),
        (
            f"- latest_trade_dates: A股 {coverage.get('a_share_trade_date') or '-'} / "
            f"港股 {coverage.get('hk_trade_date') or '-'} / 美股 {coverage.get('us_trade_date') or '-'}"
        ),
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")

    lines.extend(
        [
            "",
            "## 个股预测",
            "",
            "| 标的 | 市场 | 所在池 | 最新收盘 | 下一交易日区间 | 5日区间 | 方向偏置 | 置信度 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("equities") or []:
        next_day = item.get("next_day") or {}
        five_day = item.get("five_day") or {}
        lines.append(
            "| {subject} | {market_label} | {primary_pool} | {close} | {next_low} - {next_high} | {five_low} - {five_high} | {bias} | {confidence_label} ({confidence}) |".format(
                subject=f"{item.get('name') or '-'} / {item.get('ts_code') or '-'}",
                market_label=item.get("market_label") or "-",
                primary_pool=item.get("primary_pool") or "-",
                close=item.get("latest_close") or "-",
                next_low=next_day.get("low") or "-",
                next_high=next_day.get("high") or "-",
                five_low=five_day.get("low") or "-",
                five_high=five_day.get("high") or "-",
                bias=item.get("bias_label") or "-",
                confidence_label=item.get("confidence_label") or "-",
                confidence=item.get("confidence") or "-",
            )
        )

    lines.extend(
        [
            "",
            "## 指数代理预测",
            "",
            "| 代理 | 市场 | 成员数 | 最新值 | 下一交易日区间 | 5日区间 | 方向偏置 | 说明 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("index_proxies") or []:
        next_day = item.get("next_day") or {}
        five_day = item.get("five_day") or {}
        lines.append(
            "| {name} | {market_label} | {member_count} | {close} | {next_low} - {next_high} | {five_low} - {five_high} | {bias} | {description} |".format(
                name=item.get("name") or "-",
                market_label=item.get("market_label") or "-",
                member_count=item.get("used_member_count") or item.get("member_count") or 0,
                close=item.get("latest_close") or "-",
                next_low=next_day.get("low") or "-",
                next_high=next_day.get("high") or "-",
                five_low=five_day.get("low") or "-",
                five_high=five_day.get("high") or "-",
                bias=item.get("bias_label") or "-",
                description=item.get("description") or "-",
            )
        )

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]

    conn = sqlite3.connect(DB_PATH)
    try:
        pool_meta = load_active_pool_meta(conn)
        equities = build_equity_items(conn, pool_meta)
        index_proxies = build_index_proxy_items(conn, pool_meta)
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "methodology": "价格动量 + 日波动 + 技术因子偏置（A/H）/ 价格动量 + 波动偏置（US）",
            "note": "这是研究用的短周期区间推演，不是带监督标签训练后的收益预测模型，也不是自动交易指令。",
            "coverage_summary": coverage_summary(pool_meta, equities, index_proxies),
            "overview_lines": build_overview_lines(equities, index_proxies),
            "equity_count": len(equities),
            "index_proxy_count": len(index_proxies),
            "equities": equities,
            "index_proxies": index_proxies,
            "equities_by_market": {
                "A": [item for item in equities if item.get("market") == "A"],
                "H": [item for item in equities if item.get("market") == "H"],
                "US": [item for item in equities if item.get("market") == "US"],
            },
        }
        output_path = OUTPUT_DIR / f"{batch_date}_price_range_forecast_snapshot.md"
        write_markdown(output_path, payload)
        registry_entry = register_snapshot(
            conn,
            entity_type="price_range_forecast_snapshot",
            entity_id=batch_date,
            status="generated" if equities else "empty",
            source=SCRIPT_NAME,
            relationships={
                "summary_rel_path": relative_to_project(output_path),
            },
            payload={
                **payload,
                "summary_rel_path": relative_to_project(output_path),
            },
            created_at=generated_at,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "price range forecast snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "equity_count": payload["equity_count"],
            "index_proxy_count": payload["index_proxy_count"],
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    print(f"Price range forecast snapshot: {relative_to_project(output_path)}")
    print(f"Active forecast equities: {payload['equity_count']}")
    print(f"Index proxies: {payload['index_proxy_count']}")


if __name__ == "__main__":
    main()
