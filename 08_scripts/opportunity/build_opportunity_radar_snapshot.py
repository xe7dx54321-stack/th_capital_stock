#!/usr/bin/env python3
"""Build an active opportunity radar snapshot from price, volume, pool, and event signals."""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, project_path, relative_to_project
from smr_agents import ensure_auto_handoff
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OPPORTUNITY_RADAR_DIR", "02_research", "opportunity_radar")
POLICY_PATH = project_path("00_control", "opportunity_engine_policy.json")
SCRIPT_NAME = "build_opportunity_radar_snapshot.py"

MARKET_LABELS = {
    "A": "A股",
    "H": "港股",
    "US": "美股",
}
MARKET_ORDER = ("A", "H", "US")
POOL_BOOST = {
    "recommended": 2.4,
    "candidate": 1.7,
    "watchlist": 1.0,
    "portfolio_seed": 0.9,
    "seed": 0.5,
    "us_benchmark": 0.4,
}


def load_policy() -> dict:
    if not POLICY_PATH.exists():
        return {}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def safe_float(value, default=None):
    if value in (None, "", "None", "nan", "-", "--"):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def pct_return(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    if current is None or previous in (None, 0):
        return None
    return current / previous * 100.0 - 100.0


def mean(values):
    rows = [safe_float(value) for value in values if safe_float(value) is not None]
    if not rows:
        return None
    return sum(rows) / len(rows)


def sample_std(values):
    rows = [safe_float(value) for value in values if safe_float(value) is not None]
    if len(rows) < 2:
        return None
    avg = sum(rows) / len(rows)
    return math.sqrt(sum((value - avg) ** 2 for value in rows) / (len(rows) - 1))


def relation_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def compact_text(value, limit=96):
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def market_from_code(ts_code, fallback=None):
    if fallback:
        return fallback
    if str(ts_code).upper().endswith(".HK"):
        return "H"
    if "." not in str(ts_code):
        return "US"
    return "A"


def load_pool_types(conn):
    if not relation_exists(conn, "stock_pool_current"):
        return {}
    rows = conn.execute(
        """
        SELECT ts_code, GROUP_CONCAT(DISTINCT pool_type), MAX(score)
        FROM stock_pool_current
        GROUP BY ts_code
        """
    ).fetchall()
    result = {}
    for ts_code, pool_csv, pool_score in rows:
        pools = [value.strip() for value in (pool_csv or "").split(",") if value.strip()]
        result[ts_code] = {
            "pool_types": pools,
            "pool_score": safe_float(pool_score),
            "primary_pool": pools[0] if pools else None,
        }
    return result


def load_factor_map(conn):
    if not relation_exists(conn, "factor_daily"):
        return {}
    latest_factor_date = conn.execute("SELECT MAX(trade_date) FROM factor_daily").fetchone()[0]
    if not latest_factor_date:
        return {}
    rows = conn.execute(
        """
        SELECT ts_code, factor_name, factor_value
        FROM factor_daily
        WHERE trade_date=?
        """,
        (latest_factor_date,),
    ).fetchall()
    factors = defaultdict(lambda: {"factor_date": latest_factor_date})
    for ts_code, factor_name, factor_value in rows:
        factors[ts_code][factor_name] = safe_float(factor_value)
    return dict(factors)


def load_decision_map(conn):
    if not relation_exists(conn, "research_decision_latest"):
        return {}
    rows = conn.execute(
        """
        SELECT ts_code, report_id, sector, title, suggested_pool, thesis_strength,
               research_quality_score, reason, file_path, decision_time
        FROM research_decision_latest
        """
    ).fetchall()
    return {
        row[0]: {
            "report_id": row[1],
            "sector": row[2],
            "title": row[3],
            "suggested_pool": row[4],
            "thesis_strength": row[5],
            "research_quality_score": safe_float(row[6]),
            "reason": row[7],
            "file_path": row[8],
            "decision_time": row[9],
        }
        for row in rows
        if row[0]
    }


def load_latest_events(conn):
    if not relation_exists(conn, "market_event_latest"):
        return {}
    rows = conn.execute(
        """
        SELECT entity_id, title, event_family, event_type, event_date,
               publish_time, importance, source_rel_path, payload_json
        FROM market_event_latest
        WHERE entity_type='stock'
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        """
    ).fetchall()
    result = {}
    for row in rows:
        ts_code = row[0]
        if not ts_code or ts_code in result:
            continue
        payload = {}
        try:
            payload = json.loads(row[8] or "{}")
        except json.JSONDecodeError:
            payload = {}
        result[ts_code] = {
            "title": row[1],
            "event_family": row[2],
            "event_type": row[3],
            "event_date": row[4],
            "publish_time": row[5],
            "importance": row[6],
            "source_rel_path": row[7],
            "summary": payload.get("summary"),
        }
    return result


def load_history(conn, ts_code, market, limit=90):
    if market == "US":
        rows = conn.execute(
            """
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
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
            SELECT trade_date, open, high, low, close, pct_chg, vol, amount
            FROM daily_bar
            WHERE ts_code=?
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (ts_code, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def load_symbols(conn):
    rows = conn.execute(
        """
        SELECT ts_code, market, MAX(trade_date) AS latest_trade_date
        FROM daily_bar
        GROUP BY ts_code, market
        """
    ).fetchall()
    symbols = [
        {
            "ts_code": row[0],
            "market": market_from_code(row[0], row[1]),
            "latest_trade_date": row[2],
        }
        for row in rows
        if row[0]
    ]
    if relation_exists(conn, "us_daily_bar"):
        us_rows = conn.execute(
            """
            SELECT symbol, MAX(trade_date) AS latest_trade_date
            FROM us_daily_bar
            GROUP BY symbol
            """
        ).fetchall()
        symbols.extend(
            {
                "ts_code": row[0],
                "market": "US",
                "latest_trade_date": row[1],
            }
            for row in us_rows
            if row[0]
        )
    return symbols


def change_from_tail(history, days):
    if len(history) <= days:
        return None
    return pct_return(history[-1].get("close"), history[-1 - days].get("close"))


def realized_volatility(history, days=20):
    if len(history) < days + 1:
        return None
    returns = []
    for prev, curr in zip(history[-days - 1 : -1], history[-days:]):
        ret = pct_return(curr.get("close"), prev.get("close"))
        if ret is not None:
            returns.append(ret / 100.0)
    vol = sample_std(returns)
    return None if vol is None else vol * math.sqrt(252)


def compute_signal_metrics(history):
    if not history:
        return {}
    latest = history[-1]
    prev_rows = history[:-1]
    latest_vol = safe_float(latest.get("vol"), 0.0) or 0.0
    latest_amount = safe_float(latest.get("amount"), 0.0) or 0.0
    avg_vol_20d = mean(row.get("vol") for row in prev_rows[-20:])
    avg_amount_20d = mean(row.get("amount") for row in prev_rows[-20:])
    previous_high_20d = max(
        [safe_float(row.get("high")) for row in prev_rows[-20:] if safe_float(row.get("high")) is not None],
        default=None,
    )
    high_60d = max(
        [safe_float(row.get("high")) for row in history[-60:] if safe_float(row.get("high")) is not None],
        default=None,
    )
    latest_close = safe_float(latest.get("close"))
    volume_ratio = latest_vol / avg_vol_20d if avg_vol_20d and avg_vol_20d > 0 else None
    amount_ratio = latest_amount / avg_amount_20d if avg_amount_20d and avg_amount_20d > 0 else None
    breakout_20d = (
        latest_close is not None
        and previous_high_20d is not None
        and latest_close > previous_high_20d
    )
    drawdown_60d_high_pct = None
    if latest_close is not None and high_60d and high_60d > 0:
        drawdown_60d_high_pct = latest_close / high_60d * 100.0 - 100.0
    return {
        "latest_trade_date": latest.get("trade_date"),
        "latest_close": latest_close,
        "latest_pct_chg": safe_float(latest.get("pct_chg")),
        "latest_vol": latest_vol,
        "latest_amount": latest_amount,
        "volume_ratio_20d": round(volume_ratio, 2) if volume_ratio is not None else None,
        "amount_ratio_20d": round(amount_ratio, 2) if amount_ratio is not None else None,
        "return_5d": change_from_tail(history, 5),
        "return_20d": change_from_tail(history, 20),
        "return_60d": change_from_tail(history, 60),
        "breakout_20d": breakout_20d,
        "drawdown_60d_high_pct": round(drawdown_60d_high_pct, 2) if drawdown_60d_high_pct is not None else None,
        "realized_volatility_20d": realized_volatility(history),
        "history_days": len(history),
    }


def event_boost(event):
    if not event:
        return 0.0
    importance = str(event.get("importance") or "").lower()
    event_type = str(event.get("event_type") or "").lower()
    boost = 0.5
    if importance in {"high", "critical"}:
        boost += 0.9
    if any(keyword in event_type for keyword in ("earnings", "announcement", "investor", "research")):
        boost += 0.5
    return boost


def pool_boost(pool_types):
    return sum(POOL_BOOST.get(pool_type, 0.0) for pool_type in (pool_types or []))


def classify_signal(metrics, factors, score):
    tags = []
    pct = metrics.get("latest_pct_chg") or 0.0
    ret_5d = metrics.get("return_5d") or 0.0
    ret_20d = metrics.get("return_20d") or 0.0
    volume_ratio = metrics.get("volume_ratio_20d") or 0.0
    rsi = factors.get("rsi_14")
    trend_strength = factors.get("trend_strength") or 0.0
    macd_hist = factors.get("macd_hist") or 0.0

    if metrics.get("breakout_20d") and volume_ratio >= 1.25:
        tags.append("breakout_with_volume")
    if trend_strength >= 3 and ret_20d > 0:
        tags.append("trend_continuation")
    if pct > 4 and volume_ratio >= 1.5:
        tags.append("price_volume_acceleration")
    if ret_20d < -8 and pct > 0 and macd_hist > 0:
        tags.append("reversal_probe")
    if rsi is not None and rsi >= 78:
        tags.append("overheat_watch")
    if score >= 14:
        tags.append("high_conviction_watch")
    if not tags:
        tags.append("watch_only")
    return tags


def compute_score(metrics, factors, pool_info, decision, event, policy):
    score = 0.0
    pct = metrics.get("latest_pct_chg") or 0.0
    ret_5d = metrics.get("return_5d") or 0.0
    ret_20d = metrics.get("return_20d") or 0.0
    volume_ratio = metrics.get("volume_ratio_20d") or 0.0
    amount_ratio = metrics.get("amount_ratio_20d") or 0.0
    trend_strength = factors.get("trend_strength") or 0.0
    rsi = factors.get("rsi_14")
    macd_hist = factors.get("macd_hist") or 0.0

    score += max(pct, 0.0) * 0.42
    score += max(ret_5d, 0.0) * 0.28
    score += max(ret_20d, 0.0) * 0.14
    score += min(volume_ratio, 6.0) * 1.35
    score += min(amount_ratio, 5.0) * 0.55
    score += trend_strength * 1.6
    if macd_hist > 0:
        score += min(macd_hist, 3.0) * 0.45
    if metrics.get("breakout_20d"):
        score += 2.0
    score += pool_boost(pool_info.get("pool_types") or [])
    if decision:
        score += 0.6
        if (decision.get("research_quality_score") or 0) >= 8:
            score += 1.0
        if decision.get("suggested_pool") == "recommended":
            score += 0.8
    score += event_boost(event)

    guards = policy.get("risk_guards") or {}
    overheat_rsi = safe_float(guards.get("overheat_rsi"), 78)
    single_day_chase = safe_float(guards.get("single_day_chase_pct"), 9.5)
    if rsi is not None and rsi >= overheat_rsi:
        score -= 1.2
    if pct >= single_day_chase:
        score -= 1.5
    return round(score, 2)


def render_why(item):
    parts = []
    metrics = item.get("metrics") or {}
    if metrics.get("breakout_20d"):
        parts.append("收盘价突破近20日高点，说明价格开始脱离旧震荡区间。")
    if metrics.get("volume_ratio_20d"):
        parts.append(f"量能约为近20日均值的 {metrics['volume_ratio_20d']:.2f} 倍，信号不是纯价格漂移。")
    if metrics.get("return_20d") is not None:
        parts.append(f"20日收益 {metrics['return_20d']:+.2f}%，可用于判断趋势延续强度。")
    if item.get("pool_types"):
        parts.append(f"当前已在 {'/'.join(item['pool_types'])}，不是完全陌生标的。")
    if item.get("latest_event_title"):
        parts.append(f"最近事件锚点：{compact_text(item['latest_event_title'], 54)}。")
    return parts[:5] or ["当前主要由多因子合成分数进入观察，但还需要补强事件或研究锚点。"]


def render_risks(item, policy):
    parts = []
    metrics = item.get("metrics") or {}
    factors = item.get("factors") or {}
    rsi = factors.get("rsi_14")
    pct = metrics.get("latest_pct_chg") or 0.0
    guards = policy.get("risk_guards") or {}
    if rsi is not None and rsi >= (safe_float(guards.get("overheat_rsi"), 78) or 78):
        parts.append(f"RSI 已到 {rsi:.1f}，短线可能有追高风险。")
    if pct >= (safe_float(guards.get("single_day_chase_pct"), 9.5) or 9.5):
        parts.append(f"单日涨幅 {pct:+.2f}% 偏大，不能把异动直接等同于买点。")
    if metrics.get("history_days", 0) < 60:
        parts.append("历史行情窗口不足60日，趋势和回测证据都偏薄。")
    if not item.get("latest_event_title"):
        parts.append("缺少新事件锚点，后续需要补公告、研报或资金流证据。")
    if not parts:
        parts.append("主要风险在于信号衰减，若量能回落且价格跌回均线，需要降级为普通观察。")
    return parts[:4]


def next_checks(item):
    checks = [
        "复核最近公告、研报和公开电话会/投资者关系材料，确认异动是否有基本面来源。",
        "下一交易日观察是否继续放量，且不快速跌回20日高点或20日均线下方。",
    ]
    if item.get("primary_pool") not in {"recommended", "candidate"}:
        checks.append("若连续两日信号保持，考虑进入 candidate/recommended 研究链，而不是直接进入组合动作。")
    else:
        checks.append("把现有研究结论和当前价格信号对齐，确认 thesis 是否出现加速或失效。")
    return checks


def build_item(conn, symbol, name_map, factors_map, pool_map, decision_map, event_map, policy):
    ts_code = symbol["ts_code"]
    market = symbol["market"]
    history = load_history(conn, ts_code, market)
    if len(history) < 22:
        return None
    metrics = compute_signal_metrics(history)
    factors = factors_map.get(ts_code, {})
    pool_info = pool_map.get(ts_code, {"pool_types": [], "primary_pool": None, "pool_score": None})
    decision = decision_map.get(ts_code)
    event = event_map.get(ts_code)
    score = compute_score(metrics, factors, pool_info, decision, event, policy)
    signal_tags = classify_signal(metrics, factors, score)
    sector = (decision or {}).get("sector")
    if not sector and pool_info.get("sector"):
        sector = pool_info.get("sector")
    if not sector:
        row = conn.execute(
            "SELECT sector FROM stock_pool_current WHERE ts_code=? AND sector IS NOT NULL LIMIT 1",
            (ts_code,),
        ).fetchone() if relation_exists(conn, "stock_pool_current") else None
        sector = row[0] if row else ""
    item = {
        "ts_code": ts_code,
        "name": name_map.get(ts_code, ts_code),
        "market": market,
        "market_label": MARKET_LABELS.get(market, market),
        "sector": sector or "",
        "opportunity_score": score,
        "signal_tags": signal_tags,
        "pool_types": pool_info.get("pool_types") or [],
        "primary_pool": pool_info.get("primary_pool"),
        "pool_score": pool_info.get("pool_score"),
        "metrics": {
            key: (round(value, 4) if isinstance(value, float) else value)
            for key, value in metrics.items()
        },
        "factors": {
            key: value
            for key, value in factors.items()
            if key in {"factor_date", "trend_strength", "rsi_14", "macd_hist", "ma_20", "ma_60", "volatility_20"}
        },
        "research_decision": decision or {},
        "latest_event_title": (event or {}).get("title"),
        "latest_event_summary": (event or {}).get("summary"),
        "latest_event_rel_path": (event or {}).get("source_rel_path"),
    }
    item["why"] = render_why(item)
    item["risks"] = render_risks(item, policy)
    item["next_checks"] = next_checks(item)
    if score >= (policy.get("candidate_thresholds") or {}).get("high_conviction_min_score", 14):
        item["radar_bucket"] = "high_conviction_watch"
    elif score >= (policy.get("candidate_thresholds") or {}).get("paper_watch_min_score", 11):
        item["radar_bucket"] = "paper_watch_candidate"
    elif score >= (policy.get("candidate_thresholds") or {}).get("radar_candidate_min_score", 9):
        item["radar_bucket"] = "radar_candidate"
    else:
        item["radar_bucket"] = "monitor_only"
    return item


def group_by_market(items, policy):
    limits = policy.get("candidate_thresholds") or {}
    per_market_limit = int(limits.get("max_candidates_per_market") or 12)
    grouped = {market: [] for market in MARKET_ORDER}
    for item in items:
        grouped.setdefault(item["market"], []).append(item)
    for market in grouped:
        grouped[market].sort(key=lambda item: (-item["opportunity_score"], item["ts_code"]))
        grouped[market] = grouped[market][:per_market_limit]
    return grouped


def sector_heatmap(items):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.get("sector") or "unknown"].append(item)
    rows = []
    for sector, rows_in_sector in grouped.items():
        rows_in_sector.sort(key=lambda item: -item["opportunity_score"])
        rows.append(
            {
                "sector": sector,
                "candidate_count": len(rows_in_sector),
                "avg_score": round(sum(item["opportunity_score"] for item in rows_in_sector) / len(rows_in_sector), 2),
                "leaders": [
                    {
                        "ts_code": item["ts_code"],
                        "name": item["name"],
                        "market": item["market"],
                        "opportunity_score": item["opportunity_score"],
                    }
                    for item in rows_in_sector[:3]
                ],
            }
        )
    rows.sort(key=lambda item: (-item["avg_score"], -item["candidate_count"], item["sector"]))
    return rows


def overview_lines(payload):
    coverage = payload["coverage_summary"]
    lines = [
        (
            f"本轮主动扫描覆盖库：A股 {coverage.get('A', 0)} 只，"
            f"港股 {coverage.get('H', 0)} 只，美股 {coverage.get('US', 0)} 只。"
        ),
        (
            f"达到机会候选阈值 {payload.get('candidate_count', 0)} 只，"
            f"其中纸面观察候选 {payload.get('paper_watch_candidate_count', 0)} 只。"
        ),
    ]
    for market in MARKET_ORDER:
        items = payload["markets"].get(market) or []
        if not items:
            continue
        top = items[0]
        lines.append(
            f"{MARKET_LABELS.get(market)}当前雷达第一名是 {top['name']} / {top['ts_code']}，"
            f"分数 {top['opportunity_score']:.2f}，标签 {'/'.join(top.get('signal_tags') or [])}。"
        )
    return lines


def render_market_section(market, items):
    lines = [f"## {MARKET_LABELS.get(market, market)}主动机会", ""]
    if not items:
        lines.extend(["- 当前没有达到候选阈值的主动机会。", ""])
        return lines
    lines.extend(
        [
            "| 标的 | 分数 | 桶 | 最新涨跌 | 5日/20日 | 量能 | 标签 | 下一步 |",
            "| --- | ---: | --- | ---: | --- | ---: | --- | --- |",
        ]
    )
    for item in items:
        metrics = item.get("metrics") or {}
        lines.append(
            "| {subject} | {score:.2f} | {bucket} | {pct:+.2f}% | {r5} / {r20} | {vol}x | {tags} | {next_check} |".format(
                subject=f"{item['name']} / {item['ts_code']}",
                score=item["opportunity_score"],
                bucket=item.get("radar_bucket") or "-",
                pct=metrics.get("latest_pct_chg") or 0.0,
                r5=f"{metrics['return_5d']:+.2f}%" if metrics.get("return_5d") is not None else "-",
                r20=f"{metrics['return_20d']:+.2f}%" if metrics.get("return_20d") is not None else "-",
                vol=f"{metrics.get('volume_ratio_20d'):.2f}" if metrics.get("volume_ratio_20d") is not None else "-",
                tags=", ".join(item.get("signal_tags") or []),
                next_check=compact_text((item.get("next_checks") or ["-"])[0], 70),
            )
        )
    lines.append("")
    return lines


def write_markdown(path, payload):
    lines = [
        "# 主动机会雷达快照",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- batch_date: {payload.get('batch_date')}",
        "- mode: paper_only",
        "- safety: 本快照只生成研究候选和纸面观察候选，不产生真实下单指令。",
        "",
        "## 核心结论",
        "",
    ]
    for line in payload.get("overview_lines") or []:
        lines.append(f"- {line}")
    lines.extend(["", "## 主题/赛道热度", ""])
    if payload.get("sector_heatmap"):
        lines.extend(["| 赛道 | 候选数 | 平均分 | 代表标的 |", "| --- | ---: | ---: | --- |"])
        for row in payload["sector_heatmap"][:10]:
            leaders = ", ".join(f"{item['name']}({item['ts_code']})" for item in row.get("leaders") or [])
            lines.append(f"| {row['sector']} | {row['candidate_count']} | {row['avg_score']:.2f} | {leaders or '-'} |")
    else:
        lines.append("- 当前没有足够强的赛道聚合信号。")
    lines.append("")
    for market in MARKET_ORDER:
        lines.extend(render_market_section(market, payload["markets"].get(market) or []))
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    policy = load_policy()
    thresholds = policy.get("candidate_thresholds") or {}
    min_score = safe_float(thresholds.get("radar_candidate_min_score"), 9.0) or 9.0
    paper_score = safe_float(thresholds.get("paper_watch_min_score"), 11.0) or 11.0
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_date = generated_at[:10]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{batch_date}_opportunity_radar_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        name_map = combined_name_map(conn)
        factors_map = load_factor_map(conn)
        pool_map = load_pool_types(conn)
        decision_map = load_decision_map(conn)
        event_map = load_latest_events(conn)
        all_symbols = load_symbols(conn)
        scored_items = []
        coverage = defaultdict(int)
        skipped = 0
        for symbol in all_symbols:
            coverage[symbol["market"]] += 1
            item = build_item(conn, symbol, name_map, factors_map, pool_map, decision_map, event_map, policy)
            if item is None:
                skipped += 1
                continue
            scored_items.append(item)

        scored_items.sort(key=lambda item: (-item["opportunity_score"], item["ts_code"]))
        candidate_items = [item for item in scored_items if item["opportunity_score"] >= min_score]
        market_groups = group_by_market(candidate_items, policy)
        payload = {
            "generated_at": generated_at,
            "batch_date": batch_date,
            "mode": "paper_only",
            "coverage_summary": {market: coverage.get(market, 0) for market in MARKET_ORDER},
            "scored_count": len(scored_items),
            "skipped_count": skipped,
            "candidate_count": len(candidate_items),
            "paper_watch_candidate_count": sum(
                1 for item in candidate_items if item["opportunity_score"] >= paper_score
            ),
            "markets": market_groups,
            "top_candidates": scored_items[:20],
            "sector_heatmap": sector_heatmap(candidate_items),
            "policy_rel_path": relative_to_project(POLICY_PATH),
        }
        payload["overview_lines"] = overview_lines(payload)
        write_markdown(output_path, payload)

        registry_entry = register_snapshot(
            conn,
            entity_type="opportunity_radar_snapshot",
            entity_id=batch_date,
            status="generated" if candidate_items else "empty",
            source=SCRIPT_NAME,
            relationships={"summary_rel_path": relative_to_project(output_path)},
            payload={**payload, "summary_rel_path": relative_to_project(output_path)},
            created_at=generated_at,
        )
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="主动机会雷达已生成，自动转交研究代理做候选解释和下一步检查。",
            created_by=SCRIPT_NAME,
        )
        conn.commit()
    finally:
        conn.close()

    log_run(
        SCRIPT_NAME,
        "success",
        "opportunity radar snapshot built",
        {
            "registry_entry_id": registry_entry["id"],
            "summary_rel_path": relative_to_project(output_path),
            "candidate_count": payload["candidate_count"],
            "paper_watch_candidate_count": payload["paper_watch_candidate_count"],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Opportunity radar snapshot: {relative_to_project(output_path)}")
    print(f"  candidate_count={payload['candidate_count']}")
    print(f"  paper_watch_candidate_count={payload['paper_watch_candidate_count']}")


if __name__ == "__main__":
    main()
