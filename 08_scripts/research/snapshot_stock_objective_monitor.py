#!/usr/bin/env python3
"""Register an objective stock-monitor snapshot decoupled from live position sizing."""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_external_research import latest_external_research_snapshot
from smr_paths import env_or_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map, relation_exists, resolve_equity_targets, split_ts_code

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
OUTPUT_DIR = env_or_project_path("SMR_OBJECTIVE_MONITOR_DIR", "02_research", "objective_monitor")

POOL_RANKS = {
    "recommended": 0,
    "candidate": 1,
    "watchlist": 2,
    "portfolio_seed": 3,
    "seed": 4,
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
        if value in (None, "") or value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def normalize_scope_label(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = []
    for char in raw:
        if char.isalnum() or char in {"-", "_"}:
            normalized.append(char.lower())
        else:
            normalized.append("_")
    return "".join(normalized).strip("_")


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


def load_focus_targets(conn, limit=20, focus_ts_codes=None, profile_name=None, pool_types=None):
    names = combined_name_map(conn)
    requested_codes = ordered_unique(focus_ts_codes or [])
    requested_pool_types = ordered_unique(pool_types or [])

    def enrich_codes(codes, focus_strategy):
        if not codes:
            return focus_strategy, []
        rows = {}
        if relation_exists(conn, "stock_pool_current"):
            placeholders = ",".join("?" for _ in codes)
            fetched = conn.execute(
                f"""
                SELECT
                    ts_code,
                    MAX(sector) AS sector,
                    MAX(score) AS max_score,
                    GROUP_CONCAT(DISTINCT pool_type) AS pool_types
                FROM stock_pool_current
                WHERE ts_code IN ({placeholders})
                GROUP BY ts_code
                """,
                codes,
            ).fetchall()
            for ts_code, sector, max_score, pool_types in fetched:
                rows[ts_code] = {
                    "sector": sector,
                    "score": max_score,
                    "pool_types": ordered_unique((pool_types or "").split(",")),
                }
        return (
            focus_strategy,
            [
                {
                    "ts_code": ts_code,
                    "name": names.get(ts_code, ts_code),
                    "sector": rows.get(ts_code, {}).get("sector"),
                    "score": rows.get(ts_code, {}).get("score"),
                    "pool_types": rows.get(ts_code, {}).get("pool_types", []),
                }
                for ts_code in codes[:limit]
            ],
        )

    if requested_codes:
        return enrich_codes(requested_codes, "explicit_ts_codes")

    if profile_name or requested_pool_types:
        resolved = resolve_equity_targets(
            conn,
            profile_name=profile_name or "amplified_analysis",
            pool_types=requested_pool_types or None,
            allowed_markets=["SZ", "SH", "BJ", "HK"],
            limit=limit,
        )
        return (
            f"profile:{profile_name or 'custom_pool_types'}",
            [
                {
                    "ts_code": item["ts_code"],
                    "name": item["name"],
                    "sector": item.get("sector"),
                    "score": item.get("score"),
                    "pool_types": ordered_unique(item.get("pool_types") or []),
                }
                for item in resolved
            ],
        )

    if relation_exists(conn, "stock_pool_current"):
        portfolio_codes = [
            row[0]
            for row in conn.execute(
                """
                SELECT DISTINCT ts_code
                FROM stock_pool_current
                WHERE pool_type='portfolio_seed'
                ORDER BY ts_code
                """
            ).fetchall()
        ]
        if portfolio_codes:
            return enrich_codes(portfolio_codes, "portfolio_seed")

        pool_rows = conn.execute(
            """
            WITH ranked AS (
                SELECT
                    ts_code,
                    MAX(sector) AS sector,
                    MAX(score) AS max_score,
                    MIN(
                        CASE pool_type
                            WHEN 'recommended' THEN 0
                            WHEN 'candidate' THEN 1
                            WHEN 'watchlist' THEN 2
                            ELSE 9
                        END
                    ) AS pool_rank,
                    GROUP_CONCAT(DISTINCT pool_type) AS pool_types
                FROM stock_pool_current
                WHERE pool_type IN ('recommended', 'candidate', 'watchlist')
                GROUP BY ts_code
            )
            SELECT ts_code, sector, max_score, pool_types
            FROM ranked
            ORDER BY pool_rank ASC, max_score DESC, ts_code ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return (
            "top_pool",
            [
                {
                    "ts_code": ts_code,
                    "name": names.get(ts_code, ts_code),
                    "sector": sector,
                    "score": max_score,
                    "pool_types": ordered_unique((pool_types or "").split(",")),
                }
                for ts_code, sector, max_score, pool_types in pool_rows
            ],
        )

    return "none", []


def latest_daily_snapshot(conn, ts_code):
    row = conn.execute(
        """
        SELECT trade_date, close, pct_chg
        FROM daily_bar
        WHERE ts_code=?
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return {}
    return {
        "trade_date": row[0],
        "close": safe_float(row[1]),
        "pct_chg": safe_float(row[2]),
    }


def latest_factor_snapshot(conn, ts_code):
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


def objective_view_and_watchpoints(daily, factors, research):
    trend_strength = safe_float(factors.get("trend_strength")) or 0.0
    rsi_14 = safe_float(factors.get("rsi_14"))
    close = safe_float(daily.get("close"))
    ma20 = safe_float(factors.get("ma_20"))
    ma60 = safe_float(factors.get("ma_60"))
    pe_ttm = safe_float(factors.get("pe_ttm"))
    net_profit_yoy = safe_float(factors.get("net_profit_yoy"))
    revenue_yoy = safe_float(factors.get("revenue_yoy"))
    target_price = safe_float((research or {}).get("target_price_yuan"))

    tags = []
    watchpoints = []

    if trend_strength >= 3:
        objective_view = "trend_follow"
        tags.append("trend_strong")
        watchpoints.append("趋势保持强势，优先跟踪回踩承接和主线催化延续。")
    elif trend_strength >= 2:
        objective_view = "trend_positive"
        tags.append("trend_positive")
        watchpoints.append("趋势仍偏正向，但需要确认是否继续站稳关键均线。")
    elif ma20 is not None and close is not None and close < ma20:
        objective_view = "repair_needed"
        tags.append("below_ma20")
        watchpoints.append("价格已回到20日线下方，先看结构修复，不急着强化结论。")
    else:
        objective_view = "observe"
        tags.append("observe")
        watchpoints.append("当前缺少足够强的趋势优势，先维持观察口径。")

    if rsi_14 is not None and rsi_14 >= 75:
        tags.append("short_term_hot")
        watchpoints.append("短线偏热，避免把单日强势直接当成中线加速。")
    elif rsi_14 is not None and rsi_14 <= 30:
        tags.append("short_term_cold")
        watchpoints.append("短线偏冷，优先确认止跌和量能，而不是先下强判断。")

    if ma20 is not None and ma60 is not None and ma20 > ma60:
        tags.append("ma20_above_ma60")
    elif ma20 is not None and ma60 is not None and ma20 <= ma60:
        tags.append("ma20_below_ma60")

    if net_profit_yoy is not None:
        if net_profit_yoy < 0:
            tags.append("earnings_pressure")
            watchpoints.append("净利润同比仍承压，后续需要核对修复是否来自真实订单兑现。")
        elif net_profit_yoy >= 20:
            tags.append("earnings_growth")
            watchpoints.append("盈利增速仍有支撑，可以继续跟踪趋势与基本面是否共振。")

    if revenue_yoy is not None and revenue_yoy < 0:
        tags.append("revenue_pressure")
    elif revenue_yoy is not None and revenue_yoy >= 15:
        tags.append("revenue_growth")

    if pe_ttm is not None and pe_ttm >= 80:
        tags.append("rich_valuation")
        watchpoints.append("估值已经不低，后续更需要业绩和订单验证来托住预期。")

    if target_price is not None and close not in (None, 0):
        target_gap_pct = (target_price - close) / close * 100
        if target_gap_pct >= 15:
            tags.append("external_view_positive")
            watchpoints.append("外部卖方观点偏积极，需结合研报时效和基本面变化综合判断。")
        elif target_gap_pct <= 5:
            tags.append("external_view_muted")
            watchpoints.append("外部预期方向偏正面但空间有限，注意预期兑现后的波动。")

    published_dt = parse_date_prefix((research or {}).get("published_at"))
    if published_dt is not None:
        age_days = (datetime.now() - published_dt).days
        if age_days >= 180:
            tags.append("research_stale")
            watchpoints.append("最新公开研报偏旧，后续更应依赖公告、季报和价格结构重新校准。")

    return objective_view, ordered_unique(tags), ordered_unique(watchpoints)


def build_item(conn, focus):
    ts_code = focus["ts_code"]
    daily = latest_daily_snapshot(conn, ts_code)
    factor_snapshot = latest_factor_snapshot(conn, ts_code)
    research = latest_external_research_snapshot(conn, ts_code) or {}
    factors = factor_snapshot["factors"]
    objective_view, signal_tags, watchpoints = objective_view_and_watchpoints(daily, factors, research)

    return {
        "ts_code": ts_code,
        "name": focus["name"],
        "sector": focus.get("sector"),
        "pool_types": focus.get("pool_types", []),
        "score": focus.get("score"),
        "latest_trade_date": daily.get("trade_date"),
        "latest_close": daily.get("close"),
        "latest_pct_chg": daily.get("pct_chg"),
        "latest_factor_trade_date": factor_snapshot["trade_date"],
        "trend_strength": safe_float(factors.get("trend_strength")),
        "rsi_14": safe_float(factors.get("rsi_14")),
        "ma_20": safe_float(factors.get("ma_20")),
        "ma_60": safe_float(factors.get("ma_60")),
        "ma_120": safe_float(factors.get("ma_120")),
        "macd_hist": safe_float(factors.get("macd_hist")),
        "volatility_20": safe_float(factors.get("volatility_20")),
        "pe_ttm": safe_float(factors.get("pe_ttm")),
        "pb": safe_float(factors.get("pb")),
        "revenue_yoy": safe_float(factors.get("revenue_yoy")),
        "net_profit_yoy": safe_float(factors.get("net_profit_yoy")),
        "objective_view": objective_view,
        "signal_tags": signal_tags,
        "watchpoints": watchpoints,
        "external_research": {
            "source_kind": research.get("source_kind"),
            "published_at": research.get("published_at"),
            "org_name": research.get("org_name"),
            "rating_name": research.get("rating_name"),
            "target_price_yuan": research.get("target_price_yuan"),
            "source_rel_path": research.get("source_rel_path"),
        },
    }


def format_number(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def write_monitor_markdown(output_path, created_at, focus_strategy, items):
    objective_view_counts = Counter(item["objective_view"] for item in items)
    lines = [
        "# SMR 标的客观监控快照",
        "",
        f"- created_at: {created_at}",
        f"- focus_strategy: {focus_strategy}",
        f"- focus_count: {len(items)}",
        f"- objective_view_counts: {dict(objective_view_counts)}",
        "",
        "## 客观监控快照",
        "",
        "| 名称 | ts_code | 板块 | 客观看法 | close | pct_chg | trend_strength | rsi_14 | 外部研究 |",
        "|------|---------|------|----------|------:|--------:|---------------:|-------:|----------|",
    ]
    for item in items:
        lines.append(
            f"| {item['name']} | {item['ts_code']} | {item['sector'] or '-'} | {item['objective_view']} | "
            f"{format_number(item['latest_close'])} | {format_number(item['latest_pct_chg'])} | "
            f"{format_number(item['trend_strength'])} | {format_number(item['rsi_14'])} | "
            f"{item['external_research'].get('source_kind') or '-'} |"
        )

    lines.extend(
        [
            "",
            "## 建议动作",
            "",
            "- 这份快照只回答“标的现在客观上怎么看”，不回答“你该下多大仓位”。",
            "- 如果 `objective_view`（客观看法）转弱，先调整观察和研究优先级，再决定是否影响组合执行。",
            "- 如果公开研报偏旧，就把公告、季报和价格结构放在更高优先级。",
            "",
            "## 逐票明细",
            "",
        ]
    )

    for item in items:
        lines.extend(
            [
                f"### {item['name']} / {item['ts_code']}",
                "",
                f"- sector: `{item['sector'] or '-'}`",
                f"- pool_types: `{','.join(item['pool_types']) or '-'}`",
                f"- latest_trade_date: `{item['latest_trade_date'] or '-'}`",
                f"- latest_close: `{format_number(item['latest_close'])}`",
                f"- latest_pct_chg: `{format_number(item['latest_pct_chg'])}`",
                f"- trend_strength: `{format_number(item['trend_strength'])}`",
                f"- rsi_14: `{format_number(item['rsi_14'])}`",
                f"- ma_20 / ma_60 / ma_120: `{format_number(item['ma_20'])}` / `{format_number(item['ma_60'])}` / `{format_number(item['ma_120'])}`",
                f"- pe_ttm / pb: `{format_number(item['pe_ttm'])}` / `{format_number(item['pb'])}`",
                f"- revenue_yoy / net_profit_yoy: `{format_number(item['revenue_yoy'])}` / `{format_number(item['net_profit_yoy'])}`",
                f"- objective_view: `{item['objective_view']}`",
                f"- signal_tags: `{','.join(item['signal_tags']) or '-'}`",
                f"- external_research.source_kind: `{item['external_research'].get('source_kind') or '-'}`",
                f"- external_research.published_at: `{item['external_research'].get('published_at') or '-'}`",
                f"- external_research.org_name: `{item['external_research'].get('org_name') or '-'}`",
                f"- external_research.rating_name: `{item['external_research'].get('rating_name') or '-'}`",
                f"- external_research.target_price_yuan: `{format_number(safe_float(item['external_research'].get('target_price_yuan')))}`",
                f"- external_research.source_rel_path: `{item['external_research'].get('source_rel_path') or '-'}`",
                "",
            ]
        )
        for watchpoint in item["watchpoints"]:
            lines.append(f"- {watchpoint}")
        lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create objective stock-monitor snapshot")
    parser.add_argument("--ts-code", action="append", help="Specific ts_code to monitor; can be repeated")
    parser.add_argument("--profile", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--label", help="Optional label suffix for expanded-scope snapshot outputs")
    parser.add_argument("--skip-handoff", action="store_true", help="Skip auto handoff creation for this snapshot")
    parser.add_argument("--limit", type=int, default=20, help="Maximum stocks to include when not explicitly specified")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = normalize_scope_label(args.label)
    entity_id = created_at[:10] if not label else f"{created_at[:10]}__{label}"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{entity_id}_stock_objective_monitor.md"

    conn = sqlite3.connect(DB_PATH)
    focus_strategy, focus_targets = load_focus_targets(
        conn,
        limit=args.limit,
        focus_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
    )
    items = [build_item(conn, focus) for focus in focus_targets]
    write_monitor_markdown(output_path, created_at, focus_strategy, items)

    objective_view_counts = Counter(item["objective_view"] for item in items)
    registry_entry = register_snapshot(
        conn,
        entity_type="stock_objective_monitor_snapshot",
        entity_id=entity_id,
        status="recorded" if items else "empty",
        source="snapshot_stock_objective_monitor.py",
        relationships={
            "monitor_rel_path": relative_to_project(output_path),
        },
        payload={
            "focus_strategy": focus_strategy,
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "label": label,
            "requested_focus_count": len(args.ts_code or []),
            "focus_count": len(items),
            "objective_view_counts": dict(objective_view_counts),
            "monitor_rel_path": relative_to_project(output_path),
            "items": items,
        },
        created_at=created_at,
    )
    handoff_result = {"reason": "skip_handoff_flag", "handoff": None}
    if not args.skip_handoff:
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="标的客观监控快照已更新，自动转交 Hermes-like 研究代理补充解释并同步调度。",
            created_by="snapshot_stock_objective_monitor.py",
        )
    conn.commit()
    conn.close()

    log_run(
        "snapshot_stock_objective_monitor.py",
        "success",
        "stock objective monitor snapshotted",
        {
            "entity_id": entity_id,
            "focus_strategy": focus_strategy,
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "label": label,
            "focus_count": len(items),
            "monitor_rel_path": relative_to_project(output_path),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Stock objective monitor snapshot registered: {entity_id}")
    print(f"Monitor file: {output_path}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
