#!/usr/bin/env python3
"""
Phase 151 - News/Event Scanner for Auto-Discovery (BL-151-01)

【小白讲解】
这个模块做的事情：
1. 从数据库里的 news_items 表，查询最近一段时间的新闻
2. 把新闻里提到的股票代码都提取出来
3. 过滤掉已经在我们股票池里的代码
4. 剩下的就是"新闻里经常提到，但我们还没覆盖"的股票
5. 按提及频率排序，输出新发现候选列表

【为什么要这样做】
新闻中出现多的股票，往往是市场热点或者有重要事件。
及时发现这些股票，可以帮我们抢在别人前面研究它们。
"""
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta

# 复用 smr_paths 的 project_root 获取数据库路径
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smr_paths import project_path

DB_PATH = project_path("01_data", "db", "smr.db")


def _detect_market(ts_code: str) -> str:
    """根据代码判断市场。

    【小白讲解】
    - 纯字母 = 美股（如 NVDA、AMZN）
    - .HK 结尾 = 港股（如 09988.HK）
    - .BJ 结尾 = 北交所
    - 其他带 .SH/.SZ = A股
    """
    if not ts_code:
        return "UNKNOWN"
    if "." not in ts_code:
        # 纯字母 = 美股
        if ts_code[0].isalpha():
            return "US"
        return "UNKNOWN"
    code, market = ts_code.split(".", 1)
    return market.upper()


def scan_news_for_new_tickers(days: int = 30, min_mentions: int = 2, max_results: int = 20) -> dict:
    """从新闻中发现新的候选股票。

    Args:
        days: 往前查多少天的新闻（默认30天）
        min_mentions: 最少被提及几次才算候选（默认2次，防止偶发新闻）
        max_results: 最多返回几只（默认20只）

    Returns:
        包含扫描结果的字典，格式与 phase151_discovery_queue 兼容
    """
    conn = sqlite3.connect(DB_PATH)

    # 1. 获取当前已覆盖的股票池代码
    covered_codes = set()
    rows = conn.execute(
        "SELECT ts_code FROM stock_pool_current WHERE pool_type != 'blacklist'"
    ).fetchall()
    for r in rows:
        if r[0]:
            covered_codes.add(r[0])

    # 【小白讲解】
    # "已覆盖"指的是已经在评分流程中被处理的股票。
    # 我们通过 stock_pool_current 表来判断——只有在候选池/观察池/推荐池
    # 里的股票才算"已覆盖"，有价格数据但没评分的不算。
    # 这样 AMZN 这种有价格+因子但还没进评分流程的股票才能被发现。

    # 2. 查询最近 N 天的新闻，提取 tickers_json
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    news_rows = conn.execute(
        """
        SELECT title, tickers_json, published_at, source_key, url
        FROM news_items
        WHERE published_at >= ?
        AND tickers_json IS NOT NULL
        AND tickers_json != '[]'
        AND tickers_json != 'null'
        ORDER BY published_at DESC
        """,
        (cutoff,),
    ).fetchall()

    # 3. 统计每个 ticker 的出现频率
    ticker_counter = Counter()
    ticker_articles = {}  # ticker -> [(title, published_at, source)]

    for title, tickers_json, published_at, source_key, url in news_rows:
        try:
            tickers = json.loads(tickers_json) if tickers_json else []
        except (json.JSONDecodeError, TypeError):
            continue

        for t in tickers:
            if not t or t in covered_codes:
                continue
            ticker_counter[t] += 1
            if t not in ticker_articles:
                ticker_articles[t] = []
            ticker_articles[t].append({
                "title": title[:100],
                "published_at": published_at,
                "source": source_key,
            })

    conn.close()

    # 4. 过滤并排序
    candidates = []
    for ticker, count in ticker_counter.most_common(max_results * 2):
        if count < min_mentions:
            break

        # 判断市场
        market = _detect_market(ticker)

        # 找最近一条新闻作为触发原因
        latest = ticker_articles.get(ticker, [{}])[0]
        trigger = latest.get("title", "") or "多次出现在近期新闻中"

        # 简单的主题分类（根据新闻来源和关键词）
        if market == "US":
            theme = "US科技股热点"
        elif market == "HK":
            theme = "港股市场热点"
        else:
            theme = "A股市场热点"

        candidates.append({
            "ticker": ticker,
            "name": _ticker_to_name(ticker),
            "market": market,
            "discovery_source": "news_event",
            "trigger": trigger,
            "news_mentions": count,
            "priority": _calc_priority(count, market),
            "status": "new",
            "latest_news_at": latest.get("published_at", ""),
            "latest_news_title": latest.get("title", "")[:80],
        })

        if len(candidates) >= max_results:
            break

    # 5. 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["news_mentions"]))

    return {
        "phase151_news_scanner": {
            "candidates_discovered": len(candidates),
            "candidates": candidates,
            "scan_days": days,
            "min_mentions": min_mentions,
            "total_news_queried": len(news_rows),
            "unique_tickers_found": len(ticker_counter),
            "already_covered_filtered": sum(1 for _ in ticker_counter if _ in covered_codes),
            "mock_used": False,
            "fixture_used": False,
        }
    }


def _ticker_to_name(ticker: str) -> str:
    """根据 ticker 返回一个简化的中文名称（用于展示）。"""
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
        "TXN": "德州仪器",
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


def _calc_priority(count: int, market: str) -> str:
    """根据提及次数和市场计算优先级。

    【小白讲解】
    - 新闻提 10+ 次 = 高优先级（市场大热点）
    - 新闻提 5-9 次 = 中优先级
    - 新闻提 2-4 次 = 低优先级
    - 美股整体优先级 +0.5
    """
    if market == "US":
        count = count * 1.5  # 美股加权

    if count >= 15:
        return "high"
    elif count >= 5:
        return "medium"
    else:
        return "low"


def build_news_scanner_result() -> dict:
    """供 phase151_discovery_dashboard 调用的入口函数。"""
    result = scan_news_for_new_tickers(days=30, min_mentions=2, max_results=20)
    return result


if __name__ == "__main__":
    result = build_news_scanner_result()
    scanner = result["phase151_news_scanner"]
    print("=" * 60)
    print("Phase 151 新闻扫描结果（BL-151-01）")
    print("=" * 60)
    print(f"扫描天数: {scanner['scan_days']} 天")
    print(f"查询新闻数: {scanner['total_news_queried']} 条")
    print(f"发现不同tickers: {scanner['unique_tickers_found']} 个")
    print(f"已被覆盖过滤: {scanner['already_covered_filtered']} 个")
    print(f"新候选股票: {scanner['candidates_discovered']} 只")
    print()
    print("%-10s %-6s %-8s %-8s %s" % ("股票代码", "市场", "优先级", "提及次数", "触发标题"))
    print("-" * 60)
    for c in scanner["candidates"]:
        print("%-10s %-6s %-8s %-8d %s" % (
            c["ticker"],
            c["market"],
            c["priority"],
            c["news_mentions"],
            c["trigger"][:35],
        ))
