#!/usr/bin/env python3
"""Build symbol-level rotation candidates from current opportunity pool vs portfolio seed."""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
for path in (LIB_DIR, RESEARCH_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_strategy_watch_cards import strategy_summary_item
from snapshot_stock_objective_monitor import build_item
from smr_agents import DB_PATH, ensure_auto_handoff
from smr_official_materials import summarize_official_materials
from smr_paths import env_or_project_path, relative_to_project
from smr_public_analyst_digest import summarize_public_analyst_signal
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map, relation_exists

OUTPUT_DIR = env_or_project_path("SMR_PORTFOLIO_ROTATION_DIR", "04_portfolio", "rotation")

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
    "none": "未分层",
    "trend_follow": "趋势跟随",
    "trend_positive": "趋势偏正",
    "observe": "观察",
    "repair_needed": "等待修复",
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
    "high": "高",
    "medium": "中",
    "low": "低",
    "same_sector_upgrade": "同主线做强换弱",
    "cross_sector_mainline_switch": "跨主题切主线",
    "cross_sector_probe": "跨主题试探",
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


def supports_public_analyst_signal(ts_code):
    text = str(ts_code or "").upper()
    return bool(text) and not text.endswith((".SZ", ".SH", ".BJ"))


def public_signal_label_text(value):
    return PUBLIC_SIGNAL_LABELS.get(value, value or "-")


def primary_pool(pool_types):
    ordered = ["recommended", "candidate", "watchlist", "portfolio_seed", "seed"]
    values = set(pool_types or [])
    for item in ordered:
        if item in values:
            return item
    return "none"


def load_pool_rows(conn, include_pool_types):
    if not relation_exists(conn, "stock_pool_current"):
        return []

    placeholders = ",".join("?" for _ in include_pool_types)
    rows = conn.execute(
        f"""
        SELECT
            ts_code,
            MAX(sector) AS sector,
            MAX(score) AS score,
            GROUP_CONCAT(DISTINCT pool_type) AS pool_types
        FROM stock_pool_current
        WHERE pool_type IN ({placeholders})
        GROUP BY ts_code
        """,
        include_pool_types,
    ).fetchall()
    names = combined_name_map(conn)
    results = []
    for ts_code, sector, score, pool_types in rows:
        values = ordered_unique((pool_types or "").split(","))
        results.append(
            {
                "ts_code": ts_code,
                "name": names.get(ts_code, ts_code),
                "sector": sector,
                "score": safe_float(score),
                "pool_types": values,
                "primary_pool": primary_pool(values),
            }
        )
    return results


def quality_score(item):
    priority = (item.get("priority") or {}).get("label", "low")
    trend_state = (item.get("trend_state") or {}).get("label", "neutral_observe")
    valuation_pressure = (item.get("valuation_pressure") or {}).get("label", "unknown")
    research_staleness = (item.get("research_staleness") or {}).get("label", "missing")
    official_freshness = (item.get("official_material") or {}).get("freshness_label", "missing")
    transcript_freshness = (item.get("public_transcript") or {}).get("freshness_label", "missing")
    public_signal_label = (item.get("public_analyst_signal") or {}).get("stance_label", "missing")
    if not supports_public_analyst_signal(item.get("ts_code")):
        public_signal_label = "neutral"
    objective_view = item.get("objective_view")
    signal_tags = set(item.get("signal_tags") or [])
    primary = item.get("primary_pool") or "none"
    trend_strength = safe_float(item.get("trend_strength")) or 0.0

    score = 0.0
    score += {"recommended": 2.5, "candidate": 1.5, "watchlist": 0.5}.get(primary, 0.0)
    score += {"trend_follow": 2.5, "trend_positive": 1.5, "observe": 0.5, "repair_needed": -1.0}.get(
        objective_view, 0.0
    )
    score += {"high": 2.0, "medium": 1.0, "low": 0.0}.get(priority, 0.0)
    score += min(trend_strength, 3.0) * 0.5
    score += {"trend_strong": 0.8, "trend_hot": 0.5, "trend_positive": 0.4, "under_ma60": -0.2, "repair_below_ma20": -0.8}.get(
        trend_state, 0.0
    )
    score += {"fresh": 1.0, "usable": 0.5, "aging": 0.0, "stale": -0.5, "missing": -1.0}.get(
        research_staleness, -0.5
    )
    score += {"fresh_hot": 1.0, "fresh": 0.7, "usable": 0.3, "stale": -0.2, "missing": -0.5}.get(
        official_freshness, -0.3
    )
    score += {"fresh": 0.5, "usable": 0.2, "stale": -0.2, "missing": -0.4}.get(transcript_freshness, -0.2)
    score += {
        "supportive_strong": 0.8,
        "supportive": 0.5,
        "neutral_watch": 0.2,
        "neutral": 0.0,
        "stretched": -0.4,
        "cautious": -0.8,
        "missing": -0.2,
    }.get(public_signal_label, 0.0)
    score += {"low": 0.2, "medium": -0.2, "high": -0.8, "unknown": -0.3}.get(valuation_pressure, -0.2)
    if "earnings_growth" in signal_tags:
        score += 0.4
    if "revenue_growth" in signal_tags:
        score += 0.2
    if "earnings_pressure" in signal_tags:
        score -= 0.6
    if "short_term_hot" in signal_tags:
        score -= 0.2
    if "research_stale" in signal_tags:
        score -= 0.3
    return round(score, 2)


def rotation_out_score(item):
    objective_view = item.get("objective_view")
    trend_state = (item.get("trend_state") or {}).get("label", "neutral_observe")
    valuation_pressure = (item.get("valuation_pressure") or {}).get("label", "unknown")
    research_staleness = (item.get("research_staleness") or {}).get("label", "missing")
    official_freshness = (item.get("official_material") or {}).get("freshness_label", "missing")
    transcript_freshness = (item.get("public_transcript") or {}).get("freshness_label", "missing")
    public_signal_label = (item.get("public_analyst_signal") or {}).get("stance_label", "missing")
    if not supports_public_analyst_signal(item.get("ts_code")):
        public_signal_label = "neutral"
    primary = item.get("primary_pool") or "none"
    signal_tags = set(item.get("signal_tags") or [])

    score = 0.0
    score += {"repair_needed": 4.0, "observe": 2.5, "trend_positive": 1.0, "trend_follow": 0.0}.get(
        objective_view, 1.0
    )
    score += {"repair_below_ma20": 1.5, "under_ma60": 1.0, "neutral_observe": 0.5}.get(trend_state, 0.0)
    score += {"stale": 1.0, "missing": 1.2, "aging": 0.6, "usable": 0.2, "fresh": 0.0}.get(
        research_staleness, 0.3
    )
    score += {"stale": 0.6, "missing": 0.9, "usable": 0.2, "fresh": 0.0, "fresh_hot": 0.0}.get(
        official_freshness, 0.2
    )
    score += {"missing": 0.8, "stale": 0.6, "usable": 0.2, "fresh": 0.0}.get(transcript_freshness, 0.2)
    score += {
        "cautious": 1.0,
        "stretched": 0.7,
        "missing": 0.2,
        "neutral_watch": -0.1,
        "supportive": -0.3,
        "supportive_strong": -0.5,
    }.get(public_signal_label, 0.0)
    if primary not in {"recommended", "candidate"}:
        score += 1.0
    if valuation_pressure == "high" and objective_view != "trend_follow":
        score += 0.8
    if "earnings_pressure" in signal_tags:
        score += 0.8
    if "short_term_hot" in signal_tags and objective_view != "trend_follow":
        score += 0.4
    return round(score, 2)


def rotation_in_score(item):
    score = quality_score(item)
    primary = item.get("primary_pool") or "none"
    objective_view = item.get("objective_view")
    score += {"recommended": 1.0, "candidate": 0.5}.get(primary, 0.0)
    if objective_view in {"trend_follow", "trend_positive"}:
        score += 0.5
    return round(score, 2)


def fit_label(add_item, remove_item):
    if add_item.get("sector") and add_item.get("sector") == remove_item.get("sector"):
        return "same_sector_upgrade"
    if add_item.get("primary_pool") == "recommended":
        return "cross_sector_mainline_switch"
    return "cross_sector_probe"


def build_positive_change(add_item, remove_item, pair_score):
    reasons = []
    if add_item.get("primary_pool") != remove_item.get("primary_pool"):
        reasons.append(
            f"机会池级别从 {display_label(remove_item.get('primary_pool') or 'none')} 切到 {display_label(add_item.get('primary_pool') or 'none')}。"
        )
    if safe_float(add_item.get("trend_strength")) is not None and safe_float(remove_item.get("trend_strength")) is not None:
        if safe_float(add_item.get("trend_strength")) > safe_float(remove_item.get("trend_strength")):
            reasons.append("调入腿的趋势强度更高。")
    add_research = (add_item.get("research_staleness") or {}).get("label")
    remove_research = (remove_item.get("research_staleness") or {}).get("label")
    add_official = (add_item.get("official_material") or {}).get("freshness_label")
    remove_official = (remove_item.get("official_material") or {}).get("freshness_label")
    add_transcript = (add_item.get("public_transcript") or {}).get("freshness_label")
    remove_transcript = (remove_item.get("public_transcript") or {}).get("freshness_label")
    add_public = (add_item.get("public_analyst_signal") or {}).get("stance_label")
    remove_public = (remove_item.get("public_analyst_signal") or {}).get("stance_label")
    if not supports_public_analyst_signal(add_item.get("ts_code")):
        add_public = "neutral"
    if not supports_public_analyst_signal(remove_item.get("ts_code")):
        remove_public = "neutral"
    if add_research in {"fresh", "usable"} and remove_research in {"aging", "stale", "missing"}:
        reasons.append("调入腿的研究锚点相对更可用。")
    if add_official in {"fresh_hot", "fresh", "usable"} and remove_official in {"stale", "missing"}:
        reasons.append("调入腿的官方一手材料更近，判断不容易只停留在二手信息。")
    if add_transcript in {"fresh", "usable"} and remove_transcript in {"stale", "missing"}:
        reasons.append("调入腿最近有可复核的电话会原话，管理层口径比调出腿更容易直接核对。")
    if add_public in {"supportive_strong", "supportive"} and remove_public in {"stretched", "cautious", "missing"}:
        reasons.append("调入腿的公开卖方口径更顺，预期空间也更像还没被完全打满。")
    add_flow_score = safe_float(add_item.get("capital_flow_signal_score")) or 0.0
    remove_flow_score = safe_float(remove_item.get("capital_flow_signal_score")) or 0.0
    if add_flow_score > remove_flow_score and add_item.get("capital_flow_summary"):
        reasons.append(f"调入腿的资金面更有支撑：{add_item.get('capital_flow_summary')}")
    add_event_score = safe_float(add_item.get("event_signal_score")) or 0.0
    remove_event_score = safe_float(remove_item.get("event_signal_score")) or 0.0
    if add_event_score > remove_event_score and add_item.get("event_summary"):
        reasons.append(f"调入腿最近的事件催化更清晰：{add_item.get('event_summary')}")
    if add_item.get("sector") == remove_item.get("sector"):
        reasons.append("这更像同主线内做强换弱。")
    else:
        reasons.append("这会把注意力切到当前更强的机会池。")
    reasons.append(f"结构质量改进分（quality delta，结构质量差值）约为 `{pair_score:.2f}`。")
    return reasons[:4]


def build_risk_flags(add_item, remove_item):
    flags = []
    add_trend_state = (add_item.get("trend_state") or {}).get("label")
    add_valuation = (add_item.get("valuation_pressure") or {}).get("label")
    add_research = (add_item.get("research_staleness") or {}).get("label")
    add_official = (add_item.get("official_material") or {}).get("freshness_label")
    add_transcript = (add_item.get("public_transcript") or {}).get("freshness_label")
    add_public = (add_item.get("public_analyst_signal") or {}).get("stance_label")
    if not supports_public_analyst_signal(add_item.get("ts_code")):
        add_public = "neutral"
    remove_objective = remove_item.get("objective_view")
    if add_trend_state == "trend_hot":
        flags.append("调入腿短线偏热，容易遇到追高后回踩。")
    if add_valuation == "high":
        flags.append("调入腿估值压力高，后续更依赖业绩兑现。")
    if add_research in {"stale", "missing"}:
        flags.append("调入腿的外部研究锚点不够新，需要补公告或季报。")
    if add_official in {"stale", "missing"}:
        flags.append("调入腿的官方一手材料不够新，不能只靠题材叙事下结论。")
    if add_transcript in {"stale", "missing"}:
        flags.append("调入腿缺少足够新的电话会原话锚点，管理层最新表述还没完全核对。")
    if add_public in {"stretched", "cautious"}:
        flags.append("调入腿在公开卖方口径里已经不算便宜，市场可能先把预期走了一段。")
    if add_public == "missing":
        flags.append("调入腿缺少公开卖方信号参照，暂时少了一层市场预期校验。")
    if "quarterly" in set(((add_item.get("stock_connect") or {}).get("frequencies") or [])):
        flags.append("调入腿的互联互通持仓这里更多还是季频快照，不能把它直接当短线资金表态。")
    if add_item.get("event_summary"):
        flags.append(add_item.get("event_summary"))
    if add_item.get("sector") != remove_item.get("sector"):
        flags.append("这是跨主题切换，组合风格会变化。")
    if remove_objective in {"trend_follow", "trend_positive"}:
        flags.append("调出腿本身并不算很弱，换仓确定性还要继续验证。")
    return ordered_unique(flags)[:4]


def build_rotation_pairs(add_candidates, remove_candidates, limit=3):
    pairs = []
    used_remove = set()
    for add_item in add_candidates:
        best = None
        for remove_item in remove_candidates:
            if remove_item["ts_code"] in used_remove:
                continue
            pair_score = round(add_item["rotation_in_score"] - remove_item["quality_score"] + remove_item["rotation_out_score"], 2)
            sector_bonus = 0.8 if add_item.get("sector") == remove_item.get("sector") else 0.0
            final_score = round(pair_score + sector_bonus, 2)
            candidate = {
                "add": add_item,
                "remove": remove_item,
                "fit_label": fit_label(add_item, remove_item),
                "pair_score": final_score,
            }
            if best is None or candidate["pair_score"] > best["pair_score"]:
                best = candidate
        if best is None:
            continue
        used_remove.add(best["remove"]["ts_code"])
        best["expected_positive_change"] = build_positive_change(best["add"], best["remove"], best["pair_score"])
        best["risk_flags"] = build_risk_flags(best["add"], best["remove"])
        pairs.append(best)
        if len(pairs) >= limit:
            break
    return pairs


def enrich_focus(conn, rows):
    items = []
    for row in rows:
        raw_item = build_item(conn, row)
        summary = strategy_summary_item(
            conn,
            raw_item,
            official_material=summarize_official_materials(conn, row.get("ts_code"), limit=4),
            public_analyst_signal=summarize_public_analyst_signal(conn, row.get("ts_code")),
            public_transcript=latest_public_transcript_snapshot(conn, row.get("ts_code")),
        )
        summary["primary_pool"] = row.get("primary_pool")
        summary["pool_types"] = row.get("pool_types") or []
        summary["score"] = row.get("score")
        summary["quality_score"] = quality_score(summary)
        summary["rotation_in_score"] = rotation_in_score(summary)
        summary["rotation_out_score"] = rotation_out_score(summary)
        items.append(summary)
    return items


def top_add_sort_key(item):
    return (
        -safe_float(item.get("rotation_in_score") or 0.0),
        -safe_float(item.get("quality_score") or 0.0),
        item.get("ts_code") or "",
    )


def top_remove_sort_key(item):
    return (
        -safe_float(item.get("rotation_out_score") or 0.0),
        safe_float(item.get("quality_score") or 0.0),
        item.get("ts_code") or "",
    )


def format_number(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def write_snapshot(path, created_at, holdings, opportunities, rotation_pairs):
    lines = [
        "# SMR 轮动候选快照",
        "",
        f"- created_at: {created_at}",
        f"- holdings_reference_count: {len(holdings)}",
        f"- opportunity_count: {len(opportunities)}",
        f"- rotation_pair_count: {len(rotation_pairs)}",
        "",
        "## 使用边界",
        "",
        "- 这份快照当前只做“标的级调入 / 调出建议”，不做真实仓位比例计算。",
        "- 这里的“预期正向变化”不是收益预测，而是组合结构质量的启发式提升。",
        "- 真正落地执行时，仍要叠加 `entry.py / risk_monitor_snapshot / position`（开仓门禁 / 风控快照 / 正式持仓）检查。",
        "",
        "## 优先调入候选",
        "",
        "| 名称 | ts_code | 当前池子 | 客观看法 | quality_score | rotation_in_score | 核心理由 |",
        "|------|---------|----------|----------|--------------:|------------------:|----------|",
    ]
    for item in opportunities[:5]:
        watchpoint = (item.get("auxiliary_watchpoints") or item.get("watchpoints") or ["-"])[0]
        analyst = public_signal_label_text((item.get("public_analyst_signal") or {}).get("stance_label"))
        transcript = display_label(((item.get("public_transcript") or {}).get("freshness_label") or "-"))
        lines.append(
            f"| {item['name']} | {item['ts_code']} | {display_label(item.get('primary_pool') or '-')} | {display_label(item.get('objective_view') or '-')} | "
            f"{format_number(item.get('quality_score'))} | {format_number(item.get('rotation_in_score'))} | "
            f"{watchpoint} / 资金面：{item.get('capital_flow_summary') or '-'} / 电话会稿：{transcript} / 卖方参照：{analyst} |"
        )

    lines.extend(
        [
            "",
            "## 优先调出参照",
            "",
            "| 名称 | ts_code | 当前池子 | 客观看法 | quality_score | rotation_out_score | 核心理由 |",
            "|------|---------|----------|----------|--------------:|-------------------:|----------|",
        ]
    )
    for item in holdings[:5]:
        watchpoint = (item.get("auxiliary_watchpoints") or item.get("watchpoints") or ["-"])[0]
        analyst = public_signal_label_text((item.get("public_analyst_signal") or {}).get("stance_label"))
        transcript = display_label(((item.get("public_transcript") or {}).get("freshness_label") or "-"))
        lines.append(
            f"| {item['name']} | {item['ts_code']} | {display_label(item.get('primary_pool') or '-')} | {display_label(item.get('objective_view') or '-')} | "
            f"{format_number(item.get('quality_score'))} | {format_number(item.get('rotation_out_score'))} | "
            f"{watchpoint} / 资金面：{item.get('capital_flow_summary') or '-'} / 电话会稿：{transcript} / 卖方参照：{analyst} |"
        )

    lines.extend(
        [
            "",
            "## 优先轮动对",
            "",
            "| 调入 | 调出 | 轮动类型 | pair_score | 主要意义 |",
            "|------|------|----------|-----------:|----------|",
        ]
    )
    for pair in rotation_pairs:
        lines.append(
            f"| {pair['add']['ts_code']} {pair['add']['name']} | {pair['remove']['ts_code']} {pair['remove']['name']} | "
            f"{display_label(pair['fit_label'])} | {format_number(pair['pair_score'])} | {(pair['expected_positive_change'] or ['-'])[0]} |"
        )

    lines.extend(["", "## 逐对说明", ""])
    for pair in rotation_pairs:
        add_item = pair["add"]
        remove_item = pair["remove"]
        lines.extend(
            [
                f"### 调入 {add_item['name']} / {add_item['ts_code']}  vs  调出 {remove_item['name']} / {remove_item['ts_code']}",
                "",
                f"- rotation_type: {display_label(pair['fit_label'])}",
                f"- pair_score: `{format_number(pair['pair_score'])}`",
                f"- add.primary_pool: {display_label(add_item.get('primary_pool') or '-')}",
                f"- add.objective_view: {display_label(add_item.get('objective_view') or '-')}",
                f"- add.trend_state: {display_label((add_item.get('trend_state') or {}).get('label', '-'))} / {(add_item.get('trend_state') or {}).get('summary', '-')}",
                f"- add.capital_flow: {add_item.get('capital_flow_summary') or '-'}",
                f"- add.event_summary: {add_item.get('event_summary') or '-'}",
                f"- add.official_material: {display_label(((add_item.get('official_material') or {}).get('freshness_label') or '-'))} / {((add_item.get('official_material') or {}).get('summary') or '-')}",
                f"- add.public_transcript: {display_label(((add_item.get('public_transcript') or {}).get('freshness_label') or '-'))} / {((add_item.get('public_transcript') or {}).get('summary') or '-')}",
                f"- add.public_analyst_signal: `{public_signal_label_text((add_item.get('public_analyst_signal') or {}).get('stance_label'))}` / {((add_item.get('public_analyst_signal') or {}).get('summary') or '-')}",
                f"- remove.primary_pool: {display_label(remove_item.get('primary_pool') or '-')}",
                f"- remove.objective_view: {display_label(remove_item.get('objective_view') or '-')}",
                f"- remove.trend_state: {display_label((remove_item.get('trend_state') or {}).get('label', '-'))} / {(remove_item.get('trend_state') or {}).get('summary', '-')}",
                f"- remove.capital_flow: {remove_item.get('capital_flow_summary') or '-'}",
                f"- remove.event_summary: {remove_item.get('event_summary') or '-'}",
                f"- remove.official_material: {display_label(((remove_item.get('official_material') or {}).get('freshness_label') or '-'))} / {((remove_item.get('official_material') or {}).get('summary') or '-')}",
                f"- remove.public_transcript: {display_label(((remove_item.get('public_transcript') or {}).get('freshness_label') or '-'))} / {((remove_item.get('public_transcript') or {}).get('summary') or '-')}",
                f"- remove.public_analyst_signal: `{public_signal_label_text((remove_item.get('public_analyst_signal') or {}).get('stance_label'))}` / {((remove_item.get('public_analyst_signal') or {}).get('summary') or '-')}",
                "",
                "#### 预期正向变化",
                "",
            ]
        )
        for reason in pair.get("expected_positive_change") or []:
            lines.append(f"- {reason}")
        lines.extend(["", "#### 主要风险", ""])
        for risk in pair.get("risk_flags") or ["当前没有额外风险说明。"]:
            lines.append(f"- {risk}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build current symbol-level rotation candidates")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)

    holding_rows = load_pool_rows(conn, ["portfolio_seed", "recommended", "candidate", "watchlist"])
    holding_rows = [row for row in holding_rows if "portfolio_seed" in set(row.get("pool_types") or [])]
    opportunity_rows = load_pool_rows(conn, ["recommended", "candidate"])
    holding_codes = {row["ts_code"] for row in holding_rows}
    opportunity_rows = [row for row in opportunity_rows if row["ts_code"] not in holding_codes]

    holdings = enrich_focus(conn, holding_rows)
    opportunities = enrich_focus(conn, opportunity_rows)
    holdings = sorted(holdings, key=top_remove_sort_key)
    opportunities = sorted(opportunities, key=top_add_sort_key)
    rotation_pairs = build_rotation_pairs(opportunities, holdings, limit=3)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{args.date}_rotation_candidate_snapshot.md"
    write_snapshot(output_path, created_at, holdings, opportunities, rotation_pairs)

    payload = {
        "holdings_reference_count": len(holdings),
        "opportunity_count": len(opportunities),
        "rotation_pair_count": len(rotation_pairs),
        "summary_rel_path": relative_to_project(output_path),
        "top_add_candidates": opportunities[:3],
        "top_reduce_candidates": holdings[:3],
        "rotation_pairs": rotation_pairs,
    }
    relationships = {
        "summary_rel_path": relative_to_project(output_path),
    }
    entry = register_snapshot(
        conn,
        entity_type="rotation_candidate_snapshot",
        entity_id=args.date,
        status="generated" if opportunities or rotation_pairs else "empty",
        source="build_rotation_candidates.py",
        relationships=relationships,
        payload=payload,
        created_at=created_at,
    )
    handoff_result = ensure_auto_handoff(
        conn,
        entry,
        note="轮动候选快照已更新，自动转交 Hermes-like 研究代理补充解释并同步调度。",
        created_by="build_rotation_candidates.py",
    )
    conn.commit()
    conn.close()

    log_run(
        "build_rotation_candidates.py",
        "success",
        "rotation candidates built",
        {
            "entity_id": args.date,
            "opportunity_count": len(opportunities),
            "rotation_pair_count": len(rotation_pairs),
            "summary_rel_path": relative_to_project(output_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Rotation candidate snapshot registered: {args.date}")
    print(f"Summary file: {output_path}")
    print(f"Opportunity count: {len(opportunities)}")
    print(f"Rotation pair count: {len(rotation_pairs)}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
