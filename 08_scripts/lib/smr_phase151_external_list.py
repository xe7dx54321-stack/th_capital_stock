#!/usr/bin/env python3
"""
Phase 151 - External Lists Import for Auto-Discovery (BL-151-03)

【小白讲解】
这个模块做的事情：
1. 扫描东方财富的分析师研报（eastmoney_news_search），找有研报但不在我们股票池的A股
2. 扫描 Yahoo Finance 新闻里提到的公司，找美股里被关注但未覆盖的
3. 按提及频率排序，找出最值得关注的外部候选

【数据来源】
- EastMoney 研报：涵盖大量A股，覆盖面广，质量较高
- Yahoo Finance RSS：涵盖美股为主，包括港股和中概股
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smr_paths import project_path
from smr_universe import load_active_equity_universe

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


def scan_external_lists(days: int = 30, min_mentions: int = 2, max_results: int = 15) -> dict:
    """从外部研报和新闻中发现新的候选股票。

    【小白讲解】
    这个函数扫描两类外部数据：
    1. 分析师研报（EastMoney）：找有研报覆盖但不在股票池的A股
    2. 美股新闻（Yahoo Finance RSS）：找有新闻热度但未覆盖的公司

    Args:
        days: 往前查多少天的新闻（默认30天）
        min_mentions: 最少被提及几次（避免偶发）
        max_results: 最多返回几只

    Returns:
        包含外部列表发现结果的字典
    """
    conn = sqlite3.connect(DB_PATH)

    # 1. 获取已覆盖的股票池
    covered_codes = set()
    rows = conn.execute("SELECT ts_code FROM stock_pool_current WHERE pool_type != 'blacklist'").fetchall()
    for r in rows:
        if r[0]:
            covered_codes.add(r[0])
    rows_ah = conn.execute("SELECT DISTINCT ts_code FROM daily_bar").fetchall()
    rows_us = conn.execute("SELECT DISTINCT symbol FROM us_daily_bar").fetchall()
    for r in rows_ah + rows_us:
        if r[0]:
            covered_codes.add(r[0])

    # 2. 获取 universe 信息
    try:
        universe = load_active_equity_universe(conn, include_seed=True)
    except Exception:
        universe = {}

    # 3. 获取最近 N 天的新闻
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    news_rows = conn.execute(
        """
        SELECT title, tickers_json, source_key, published_at
        FROM news_items
        WHERE published_at >= ? AND tickers_json IS NOT NULL
        AND tickers_json != '[]' AND tickers_json != 'null'
        ORDER BY published_at DESC
        """,
        (cutoff,),
    ).fetchall()

    conn.close()

    # 4. 统计每个 ticker 的出现频率和来源
    ticker_count = {}  # {ticker: total_count}
    ticker_sources = {}  # {ticker: set(sources)}
    ticker_articles = {}  # {ticker: [(title, source, published_at)]}
    ticker_market = {}  # {ticker: market}

    for title, tickers_json, source_key, published_at in news_rows:
        try:
            tickers = json.loads(tickers_json) if tickers_json else []
        except (json.JSONDecodeError, TypeError):
            continue

        for t in tickers:
            if not t or t in covered_codes:
                continue

            ticker_count[t] = ticker_count.get(t, 0) + 1
            ticker_sources.setdefault(t, set()).add(source_key)
            ticker_market[t] = _detect_market(t)
            ticker_articles.setdefault(t, []).append({
                "title": title,
                "source": source_key,
                "published_at": published_at,
            })

    # 5. 过滤并排序（优先东方财富研报，再是 Yahoo Finance）
    priority_sources = {"eastmoney_news_search": 3, "yahoo_finance_rss": 2}
    candidates = []

    for ticker in ticker_count:
        count = ticker_count[ticker]
        if count < min_mentions:
            continue

        articles = ticker_articles.get(ticker, [])
        latest = articles[0] if articles else {}

        # 计算来源加权分
        sources = ticker_sources.get(ticker, set())
        source_score = sum(priority_sources.get(s, 1) for s in sources)

        market = ticker_market.get(ticker, "UNKNOWN")

        # 判断触发原因
        source_label = "东方财富研报" if "eastmoney_news_search" in sources else \
                       "Yahoo Finance新闻" if "yahoo_finance_rss" in sources else "新闻提及"
        trigger = "[%s] %s" % (source_label, latest.get("title", "")[:50])

        # 判断优先级
        priority = "high" if count >= 5 or source_score >= 5 else \
                   "medium" if count >= 2 else "low"

        candidates.append({
            "ticker": ticker,
            "name": _ticker_to_name(ticker),
            "market": market,
            "discovery_source": "external_list",
            "trigger": trigger,
            "mention_count": count,
            "sources": list(sources),
            "priority": priority,
            "status": "new",
            "latest_article_at": latest.get("published_at", ""),
            "latest_article_title": latest.get("title", "")[:60],
        })

    # 6. 按优先级和提及次数排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda x: (
        priority_order.get(x["priority"], 3),
        -x["mention_count"],
        -len(x["sources"]),
    ))

    return {
        "phase151_external_list_importer": {
            "candidates_discovered": len(candidates),
            "candidates": candidates[:max_results],
            "scan_days": days,
            "min_mentions": min_mentions,
            "method": "analyst_report_news_correlation",
            "mock_used": False,
            "fixture_used": False,
        }
    }


def _ticker_to_name(ticker: str) -> str:
    """根据 ticker 返回简化的中文名称。"""
    name_map = {
        "AMZN": "亚马逊",
        "GOOGL": "谷歌",
        "GOOG": "谷歌",
        "META": "Meta",
        "TSLA": "特斯拉",
        "AAPL": "苹果",
        "NFLX": "奈飞",
        "AMD": "超微半导体",
        "INTC": "英特尔",
        "QCOM": "高通",
        "MU": "美光科技",
        "LRCX": "泛林集团",
        "AMAT": "应用材料",
        "KLAC": "科天",
        "SNPS": "新思科技",
        "CDNS": "楷登电子",
        "NOW": "ServiceNow",
        "CRM": "Salesforce",
        "ORCL": "甲骨文",
        "IBM": "IBM",
        "000660.KS": "SK海力士",
    }
    return name_map.get(ticker, ticker)


def build_external_list_result() -> dict:
    """供 phase151_discovery_dashboard 调用的入口函数。"""
    return scan_external_lists(days=30, min_mentions=2, max_results=15)


if __name__ == "__main__":
    result = build_external_list_result()
    importer = result["phase151_external_list_importer"]
    print("=" * 75)
    print("Phase 151 外部列表导入结果（BL-151-03）")
    print("=" * 75)
    print(f"扫描天数: {importer['scan_days']} 天")
    print(f"最少提及次数: {importer['min_mentions']}")
    print(f"新候选股票: {importer['candidates_discovered']} 只")
    print()
    print("%-12s %-6s %-8s %-10s %s" % (
        "股票代码", "市场", "优先级", "提及次数", "来源"))
    print("-" * 75)
    for c in importer["candidates"]:
        print("%-12s %-6s %-8s %-10d %s" % (
            c["ticker"], c["market"], c["priority"],
            c["mention_count"], ", ".join(c["sources"][:2])))
    print()
    print("Top 5 详情:")
    print("-" * 75)
    for c in importer["candidates"][:5]:
        print("  %s [%s] - %s" % (c["ticker"], c["market"], c["trigger"][:60]))
