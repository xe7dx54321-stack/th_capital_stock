#!/usr/bin/env python3
"""
Phase 151 - Scoring Integration (BL-151-05)

【小白讲解】
这个模块把"发现"和"评分"连接起来：
1. 接收 Phase 151 发现管线输出的候选股票
2. 检查每个候选是否有因子数据
3. 如果有 → 用价值评分器打分
4. 如果没有 → 给出"预估分"和"建议下一步动作"

【为什么重要】
发现了 AMZN 这样的热门股票后，需要知道它值不值得投资。
这个模块让发现流程自动连接到评分流程，形成闭环。

【发现的候选 -> 评分 -> 决策】
AMZN(120次新闻) → 价值评分 → 发现高价值 → 建议纳入研究
"""
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smr_paths import project_path
from smr_phase151_news_scanner import scan_news_for_new_tickers
from smr_phase151_financial_change import scan_financial_momentum
from smr_phase151_external_list import scan_external_lists

DB_PATH = project_path("01_data", "db", "smr.db")


def _detect_market(ts_code: str) -> str:
    """根据代码判断市场。"""
    if not ts_code:
        return "UNKNOWN"
    if "." not in ts_code:
        if ts_code[0].isalpha():
            return "US"
        return "UNKNOWN"
    _, market = ts_code.split(".", 1)
    return market.upper()


def _detect_price_spikes(conn: sqlite3.Connection, threshold_pct: float = 5.0) -> list:
    """检测价格异动：从 daily_bar 和 us_daily_bar 中找出最近交易日涨幅超过阈值的股票。

    参数：
        conn: 数据库连接
        threshold_pct: 涨幅阈值（默认 5%）

    返回：
        列表，每个元素是 {ticker, name, market, pct_chg, trigger, priority}
        如果在 stock_pool_current 中找到对应代码，则返回其 name；否则返回 "未知"

    【小白说明】
    这个函数扫描最近交易日的价格数据，找出涨幅超过 5% 的股票。
    大涨可能意味着：
    1. 有利好消息（业绩超预期、产品突破等）
    2. 市场情绪推动
    3. 技术面突破
    这些都是值得关注的信号。
    """
    spikes = []

    # 从 stock_pool_current 获取名称映射（避免每次都查数据库）
    name_map = {}
    pool_rows = conn.execute("SELECT ts_code, ts_code FROM stock_pool_current").fetchall()
    for row in pool_rows:
        name_map[row[0]] = row[0]  # 名称待会儿从 NAME_MAP 获取

    # 1. 检测 A股/港股 daily_bar
    ah_spikes = conn.execute("""
        SELECT ts_code, close, pct_chg, trade_date
        FROM daily_bar
        WHERE trade_date = (SELECT MAX(trade_date) FROM daily_bar)
          AND pct_chg IS NOT NULL
          AND pct_chg >= ?
        ORDER BY pct_chg DESC
        LIMIT 20
    """, (threshold_pct,)).fetchall()

    for row in ah_spikes:
        ticker = row[0]
        # 判断是 A股还是港股
        market = "HK" if ".HK" in ticker else "A"
        spikes.append({
            "ticker": ticker,
            "market": market,
            "pct_chg": round(row[2], 2),
            "trade_date": row[3],
            "priority": "high" if row[2] >= 8 else "medium",
            "trigger": f"价格异动：日内涨幅 +{row[2]:.1f}%",
        })

    # 2. 检测美股 us_daily_bar
    us_spikes = conn.execute("""
        SELECT symbol, close, pct_chg, trade_date
        FROM us_daily_bar
        WHERE trade_date = (SELECT MAX(trade_date) FROM us_daily_bar)
          AND pct_chg IS NOT NULL
          AND pct_chg >= ?
        ORDER BY pct_chg DESC
        LIMIT 20
    """, (threshold_pct,)).fetchall()

    for row in us_spikes:
        ticker = row[0]
        spikes.append({
            "ticker": ticker,
            "market": "US",
            "pct_chg": round(row[2], 2),
            "trade_date": row[3],
            "priority": "high" if row[2] >= 8 else "medium",
            "trigger": f"价格异动：日内涨幅 +{row[2]:.1f}%",
        })

    return spikes


def score_discovered_candidates(days: int = 30, max_candidates: int = 10) -> dict:
    """对发现管线输出的候选进行价值评分。

    Args:
        days: 新闻扫描天数（默认30天）
        max_candidates: 最多对几只候选进行评分

    Returns:
        包含评分结果的字典
    """
    conn = sqlite3.connect(DB_PATH)

    # 1. 获取所有发现候选（合并三个发现模块的结果）
    news_result = scan_news_for_new_tickers(days=days, min_mentions=2, max_results=max_candidates)
    financial_result = scan_financial_momentum(days=7, max_results=max_candidates)
    external_result = scan_external_lists(days=days, min_mentions=2, max_results=max_candidates)

    # === 新增：价格异动检测 ===
    price_spike_result = _detect_price_spikes(conn, threshold_pct=5.0)

    all_candidates = {}

    # 合并新闻扫描器结果
    for c in news_result["phase151_news_scanner"]["candidates"]:
        ticker = c["ticker"]
        if ticker not in all_candidates:
            all_candidates[ticker] = {
                "ticker": ticker,
                "name": c["name"],
                "market": c["market"],
                "discovery_sources": [],
                "total_news_mentions": 0,
                "priority": c["priority"],
                "primary_trigger": c["trigger"],
            }
        all_candidates[ticker]["discovery_sources"].append("news_scanner")
        all_candidates[ticker]["total_news_mentions"] += c.get("news_mentions", 0)

    # 合并财务变化检测结果
    for c in financial_result["phase151_financial_change_detector"]["candidates"]:
        ticker = c["ticker"]
        if ticker not in all_candidates:
            all_candidates[ticker] = {
                "ticker": ticker,
                "name": c["name"],
                "market": c.get("market", "US"),
                "discovery_sources": [],
                "total_news_mentions": 0,
                "priority": c["priority"],
                "primary_trigger": c["trigger"],
            }
        all_candidates[ticker]["discovery_sources"].append("financial_change")
        all_candidates[ticker]["total_news_mentions"] += c.get("news_mentions", 0)
        all_candidates[ticker]["financial_data"] = c.get("key_factors", {})

    # 合并外部列表导入结果
    for c in external_result["phase151_external_list_importer"]["candidates"]:
        ticker = c["ticker"]
        if ticker not in all_candidates:
            all_candidates[ticker] = {
                "ticker": ticker,
                "name": c["name"],
                "market": c["market"],
                "discovery_sources": [],
                "total_news_mentions": 0,
                "priority": c["priority"],
                "primary_trigger": c["trigger"],
            }
        all_candidates[ticker]["discovery_sources"].append("external_list")
        all_candidates[ticker]["total_news_mentions"] += c.get("mention_count", 0)

    # === 新增：合并价格异动检测结果 ===
    for spike in price_spike_result:
        ticker = spike["ticker"]
        if ticker not in all_candidates:
            all_candidates[ticker] = {
                "ticker": ticker,
                "name": spike.get("name", ticker),
                "market": spike["market"],
                "discovery_sources": [],
                "total_news_mentions": 0,
                "priority": spike["priority"],
                "primary_trigger": spike["trigger"],
            }
        all_candidates[ticker]["discovery_sources"].append("price_spike")
        all_candidates[ticker]["total_news_mentions"] += 50  # 价格异动赋予较高初始热度
        # 如果之前已有其他来源，保留优先级较高的那个
        if spike["priority"] == "high":
            all_candidates[ticker]["priority"] = "high"

    # 2. 对每个候选进行评分
    scored_candidates = []
    for ticker, candidate in all_candidates.items():
        # 检查因子数据
        factor_count = conn.execute(
            "SELECT COUNT(*) FROM factor_daily WHERE ts_code=?", (ticker,)
        ).fetchone()[0]

        # 检查价格数据
        has_us_bar = conn.execute(
            "SELECT COUNT(*) FROM us_daily_bar WHERE symbol=?", (ticker,)
        ).fetchone()[0]
        has_ah_bar = conn.execute(
            "SELECT COUNT(*) FROM daily_bar WHERE ts_code=?", (ticker,)
        ).fetchone()[0]

        has_price_data = has_us_bar > 0 or has_ah_bar > 0
        has_factor_data = factor_count > 0

        # 计算评分
        if has_factor_data and has_price_data:
            # 有完整数据 → 尝试用价值评分器打分
            try:
                # 动态导入避免循环
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from smr_value_framework import ValueScoreCard
                scorer = ValueScoreCard(conn)
                score_card = scorer.score(ticker)
                scoring_result = {
                    "method": "value_framework",
                    "composite_score": score_card.get("composite_score"),
                    "fundamental_quality": score_card.get("fundamental_quality"),
                    "valuation_position": score_card.get("valuation_position"),
                    "technical_momentum": score_card.get("technical_momentum"),
                    "theme_relevance": score_card.get("theme_relevance"),
                    "data_available": True,
                }
                action = _recommend_action(score_card.get("composite_score"), "full")
            except Exception:
                scoring_result = {"method": "value_framework_error", "data_available": False}
                action = "研究待定"
        elif has_price_data and not has_factor_data:
            # 有价格数据但没有因子数据 → 给出技术面参考
            try:
                from smr_value_framework import ValueScoreCard
                scorer = ValueScoreCard(conn)
                score_card = scorer.score(ticker)
                scoring_result = {
                    "method": "technical_only",
                    "composite_score": score_card.get("composite_score"),
                    "technical_momentum": score_card.get("technical_momentum"),
                    "data_available": False,
                    "note": "缺基本面因子，需要补充财务数据",
                }
                action = _recommend_action(score_card.get("composite_score"), "partial")
            except Exception:
                scoring_result = {"method": "technical_only_error", "data_available": False}
                action = "待技术面评估"
        else:
            # 完全没有数据 → 基于新闻热度和市场给出预估
            scoring_result = {
                "method": "preliminary",
                "data_available": False,
                "note": "需要先采集价格数据和财务数据",
                "news_momentum": candidate["total_news_mentions"],
            }
            action = "建议先纳入候选观察"

        scored_candidates.append({
            **candidate,
            "scoring": scoring_result,
            "action": action,
            "has_price_data": has_price_data,
            "has_factor_data": has_factor_data,
            "factor_count": factor_count,
        })

    conn.close()

    # 3. 排序（按新闻热度 + 评分）
    scored_candidates.sort(
        key=lambda x: (
            -x["total_news_mentions"],
            -(x["scoring"].get("composite_score") or 0),
            -({"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3)),
        )
    )

    return {
        "phase151_scoring_integration": {
            "candidates_scored": len(scored_candidates),
            "candidates": scored_candidates,
            "sources_used": ["news_scanner", "financial_change", "external_list", "price_spike"],
            "price_spike_count": len(price_spike_result),
            "method": "value_framework_integration",
            "mock_used": False,
            "fixture_used": False,
        }
    }


def _recommend_action(score: float, data_status: str) -> str:
    """根据评分和数据状态给出行动建议。

    【小白讲解】
    - 8-10分：强烈建议纳入研究
    - 6-8分：建议纳入研究
    - 4-6分：保持观察
    - 4分以下：暂不关注
    """
    if score is None:
        return "数据不足，待评估"
    if score >= 8.0:
        return "⭐ 强烈建议纳入核心研究"
    elif score >= 6.5:
        return "✅ 建议纳入研究"
    elif score >= 5.0:
        return "👀 保持观察"
    else:
        return "❌ 暂不关注"


def build_scoring_integration_result() -> dict:
    """供 phase151_discovery_dashboard 调用的入口函数。"""
    return score_discovered_candidates(days=30, max_candidates=10)


if __name__ == "__main__":
    result = build_scoring_integration_result()
    integration = result["phase151_scoring_integration"]
    print("=" * 80)
    print("Phase 151 评分集成结果（BL-151-05）")
    print("=" * 80)
    print(f"候选股票数: {integration['candidates_scored']}")
    print()
    print("%-10s %-8s %-12s %-8s %-6s %-15s %s" % (
        "股票代码", "市场", "发现来源", "热度", "评分", "数据状态", "行动建议"))
    print("-" * 80)
    for c in integration["candidates"]:
        score = c["scoring"].get("composite_score")
        score_str = "%.1f" % score if score else "N/A"
        data_str = "%s/%s" % (
            "✓价" if c["has_price_data"] else "✗价",
            "✓因" if c["has_factor_data"] else "✗因",
        )
        print("%-10s %-8s %-12s %-8d %-6s %-15s %s" % (
            c["ticker"],
            c["market"],
            ",".join(c["discovery_sources"]),
            c["total_news_mentions"],
            score_str,
            data_str,
            c["action"],
        ))
