#!/usr/bin/env python3
"""
主题扩展扫描管道（theme_extension pipeline）

功能：
    遍历 sector_priority_map.md 中定义的 5 大主题，
    从内置的概念关键词库匹配数据库中的标的，
    与 watchlist_registry.md 中的已有标的做差集，
    输出"主题内但未覆盖"的标的清单，写入 discovery_candidate 表。

小白讲解：
    这个脚本就像一个"星探"——按照 5 大赛道（机器人、算力芯片、光模块、AI应用、量子），
    去数据库里找属于这些赛道、但还没被我们关注的股票。
    找到后，把它们记到 discovery_candidate 表里，等后续 VFM 评分筛选。

输入：
    - sector_priority_map.md：5 大主题定义
    - watchlist_registry.md：已有标的清单
    - stock_pool_current 表：数据库中所有标的的 sector 标签
    - factor_daily 表：用因子数据辅助匹配

输出：
    - discovery_candidate 表：新发现的候选标的
    - 控制台日志：扫描结果摘要

用法：
    python 08_scripts/self_discovery/scan_theme_extension.py
    python 08_scripts/self_discovery/scan_theme_extension.py --dry-run   # 只看不写

安全约束：
    - 发现候选只写入 discovery_candidate 表
    - 永远不会自动写入 stock_pool 表
    - 需要人工批准后才能入池
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径处理
# ============================================================

# 项目根目录：本文件在 08_scripts/self_discovery/ 下，往上 3 层就是根
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 数据库路径
DB_PATH = PROJECT_ROOT / "01_data" / "db" / "smr.db"

# 控制文件路径
SECTOR_MAP_PATH = PROJECT_ROOT / "00_control" / "sector_priority_map.md"
WATCHLIST_PATH = PROJECT_ROOT / "00_control" / "watchlist_registry.md"

# 把 lib 目录加到 sys.path，方便 import smr_guard
LIB_DIR = PROJECT_ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

try:
    from smr_guard import Guard  # noqa: E402
except ImportError:
    # import 失败时降级处理：视为开关未启用（安全默认）
    Guard = None


# ============================================================
# Guard 门禁开关检查（SPEC 2 AC-6）
# ============================================================

def check_self_discovery_enabled() -> bool:
    """
    检查 smr_guard 的 self_discovery_enabled 开关是否启用。

    小白讲解：检查"自主发现管线"的门禁开关是不是开着。
    - True：可以正常扫描
    - False：开发模式默认关闭，扫描脚本应该 early-exit（提前退出）

    返回：
        bool：True 表示启用，False 表示禁用
    """
    if Guard is None:
        # import 失败，返回安全默认值（禁用）
        return False
    return bool(Guard.SAFETY_BOUNDARY.get("self_discovery_enabled", False))


# ============================================================
# 5 大主题的概念关键词库
#
# 小白讲解：每个主题下面列了一些"关键词"，
# 如果一只股票的名字或 sector 标签里包含这些关键词，
# 就认为它属于这个主题。
# ============================================================

THEME_KEYWORDS = {
    "embodied_ai": {
        "name": "具身智能/机器人",
        "keywords": [
            "机器人", "谐波", "减速器", "伺服", "具身",
            "拓普", "绿的", "汇川", "鸣志", "三花", "卧龙",
            "领益", "奥比", "丰立", "中大",
        ],
    },
    "semiconductor_compute": {
        "name": "半导体/算力芯片",
        "keywords": [
            "半导体", "算力", "芯片", "GPU", "CPU", "AI芯片",
            "海光", "寒武纪", "澜起", "兆易", "华大九天", "芯原",
            "中芯", "华虹", "北方华创", "中微", "长川", "沪硅",
            "紫光", "韦尔", "卓胜", "圣邦", "思瑞浦",
        ],
    },
    "semiconductor_photonics": {
        "name": "光模块/CPO",
        "keywords": [
            "光模块", "CPO", "光芯片", "光引擎", "硅光",
            "中际", "新易盛", "天孚", "光迅", "光库",
            "曙光数创", "英维克", "太辰光", "华工科技",
            "博创科技", "铭普光磁", "剑桥科技",
        ],
    },
    "ai_agent": {
        "name": "AI Agent/应用",
        "keywords": [
            "AI应用", "AI Agent", "人工智能", "大模型",
            "讯飞", "金山", "泛微", "商汤", "百度", "阿里",
            "腾讯", "微软", "Salesforce", "ServiceNow",
            "万兴科技", "福昕软件", "致远互联",
        ],
    },
    "quantum": {
        "name": "量子/前沿科学",
        "keywords": [
            "量子", "量子通信", "量子计算", "量子加密",
            "国盾", "IonQ", "Rigetti", "D-Wave", "本源",
            "国仪量子", "科大国创",
        ],
    },
}


# ============================================================
# 解析 Markdown 控制文件
# ============================================================

def parse_watchlist_registry(filepath: Path) -> set:
    """
    从 watchlist_registry.md 中解析出所有已覆盖的标的代码。

    小白讲解：读 watchlist_registry.md 文件里的表格，
    把所有股票代码提取出来，做成一个集合（set）。
    这样后续可以快速判断"这只股票是不是已经关注了"。

    参数：
        filepath: watchlist_registry.md 的路径

    返回：
        set：已覆盖标的代码集合，如 {"300308.SZ", "688041.SH", ...}
    """
    if not filepath.exists():
        print(f"[警告] watchlist_registry.md 不存在：{filepath}")
        return set()

    content = filepath.read_text(encoding="utf-8")
    codes = set()

    # 匹配表格行中的股票代码
    # A股格式：6位数字，如 300308
    # 美股格式：纯字母，如 NVDA
    # 港股格式：5位数字，如 09980
    for match in re.finditer(r"\|\s*(\d{5,6}|[A-Z]{2,6})\s*\|", content):
        code = match.group(1)
        # A股代码补全后缀
        if re.match(r"^\d{6}$", code):
            if code.startswith(("6", "9")):
                codes.add(f"{code}.SH")
            else:
                codes.add(f"{code}.SZ")
        elif re.match(r"^\d{5}$", code):
            codes.add(f"{code}.HK")
        else:
            codes.add(code)

    return codes


def parse_watchlist_with_names(filepath: Path) -> list:
    """
    从 watchlist_registry.md 中解析出标的代码、名称和 sector。

    小白讲解：和 parse_watchlist_registry 类似，但不仅提取代码，
    还提取名称和赛道标签。用于后续做主题扩展——
    比如已知"绿的谐波"属于 embodied_ai 主题，
    可以从关键词库里找到同主题但不在 watchlist 里的其他标的。

    参数：
        filepath: watchlist_registry.md 的路径

    返回：
        list：每条记录是 {"ts_code": ..., "name": ..., "sector": ..., "market": ...}
    """
    if not filepath.exists():
        return []

    content = filepath.read_text(encoding="utf-8")
    results = []

    # 匹配表格行：| Code | Name | Sector | Pool | Added |
    for match in re.finditer(
        r"\|\s*(\d{5,6}|[A-Z]{2,6})\s*\|\s*([^|]+)\|\s*([^|]+)\|",
        content
    ):
        raw_code = match.group(1).strip()
        name = match.group(2).strip()
        sector = match.group(3).strip()

        # 补全代码后缀
        if re.match(r"^\d{6}$", raw_code):
            if raw_code.startswith(("6", "9")):
                ts_code = f"{raw_code}.SH"
            else:
                ts_code = f"{raw_code}.SZ"
        elif re.match(r"^\d{5}$", raw_code):
            ts_code = f"{raw_code}.HK"
        else:
            ts_code = raw_code

        # 跳过表头行
        if name.lower() == "name" or raw_code.lower() == "code":
            continue

        results.append({
            "ts_code": ts_code,
            "name": name,
            "sector": sector,
            "market": determine_market(ts_code),
        })

    return results


def parse_sector_priority_map(filepath: Path) -> list:
    """
    从 sector_priority_map.md 中解析出 5 大主题的 key 列表。

    小白讲解：读 sector_priority_map.md 文件，
    把 5 个主题的 key（如 embodied_ai、semiconductor_compute）提取出来。

    参数：
        filepath: sector_priority_map.md 的路径

    返回：
        list：主题 key 列表，如 ["embodied_ai", "semiconductor_compute", ...]
    """
    if not filepath.exists():
        print(f"[警告] sector_priority_map.md 不存在：{filepath}")
        return list(THEME_KEYWORDS.keys())

    content = filepath.read_text(encoding="utf-8")
    sectors = []
    for match in re.finditer(r"\|\s*(\w+)\s*\|", content):
        key = match.group(1)
        if key in THEME_KEYWORDS and key not in sectors:
            sectors.append(key)

    # 如果没解析到，用默认的主题列表
    if not sectors:
        sectors = list(THEME_KEYWORDS.keys())

    return sectors


# ============================================================
# 数据库查询
# ============================================================

def get_db_connection():
    """
    获取 SQLite 数据库连接。

    返回：
        sqlite3.Connection 对象
    """
    if not DB_PATH.exists():
        print(f"[错误] 数据库不存在：{DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_all_stocks_with_sector(conn) -> list:
    """
    从 stock_pool_current 视图读取所有标的及其 sector 标签。

    小白讲解：从数据库里把所有股票的代码、名称和所属赛道都拉出来。

    参数：
        conn: 数据库连接

    返回：
        list：每条记录是 {"ts_code": ..., "sector": ..., "pool_type": ...}
    """
    # 先检查表是否存在
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_pool_current'"
    )
    if cursor.fetchone() is None:
        # stock_pool_current 是视图，可能还没创建
        # 尝试直接从 stock_pool 表查
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_pool'"
        )
        if cursor.fetchone() is None:
            print("[警告] stock_pool 表不存在，无法获取标的列表")
            return []

        # 从 stock_pool 表取最新状态
        rows = conn.execute("""
            SELECT DISTINCT ts_code, sector, pool_type
            FROM stock_pool
            WHERE status = 'active'
            ORDER BY ts_code
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT DISTINCT ts_code, sector, pool_type
            FROM stock_pool_current
            ORDER BY ts_code
        """).fetchall()

    return [dict(row) for row in rows]


def get_stock_names(conn, tickers: list) -> dict:
    """
    批量获取股票名称。

    小白讲解：给一堆股票代码，查出它们的中文名称。

    参数：
        conn: 数据库连接
        tickers: 股票代码列表

    返回：
        dict：{代码: 名称} 映射
    """
    if not tickers:
        return {}

    # 尝试从 stock_pool 表的 added_reason 字段或研究卡中找名称
    # 如果找不到，就用代码本身
    names = {}
    for ticker in tickers:
        names[ticker] = ticker  # 默认用代码

    # 尝试从 stock_pool 表查名称
    try:
        placeholders = ",".join(["?" for _ in tickers])
        rows = conn.execute(f"""
            SELECT ts_code, added_reason FROM stock_pool
            WHERE ts_code IN ({placeholders})
            GROUP BY ts_code
        """, tickers).fetchall()
        for row in rows:
            reason = row["added_reason"] or ""
            # added_reason 里可能包含名称信息，尝试提取
            # 格式可能是 "名称-入池原因" 或就是名称
            if reason:
                names[row["ts_code"]] = reason.split("-")[0].strip() or row["ts_code"]
    except Exception:
        pass

    return names


# ============================================================
# 主题匹配逻辑
# ============================================================

def match_stock_to_theme(ts_code: str, sector: str, stock_name: str, themes: list) -> str | None:
    """
    判断一只股票属于哪个主题。

    小白讲解：看这只股票的赛道标签和名字，
    如果里面包含了某个主题的关键词，就认为它属于这个主题。
    比如名字叫"中际旭创"，里面有"中际"这个光模块关键词，
    就归入 semiconductor_photonics 主题。

    参数：
        ts_code: 股票代码
        sector: 数据库里的 sector 标签
        stock_name: 股票名称
        themes: 要匹配的主题 key 列表

    返回：
        匹配到的主题 key，没匹配到返回 None
    """
    text = f"{sector} {stock_name} {ts_code}"

    for theme_key in themes:
        theme_config = THEME_KEYWORDS.get(theme_key)
        if not theme_config:
            continue

        # 如果 sector 直接就是主题 key，直接匹配
        if sector == theme_key:
            return theme_key

        # 用关键词匹配
        for keyword in theme_config["keywords"]:
            if keyword in text:
                return theme_key

    return None


# 通用词集合：这些词是行业概念词，不是公司名，不能作为候选标的
# 小白讲解：像"芯片"、"光模块"这种词是行业通用词，
# 不是某家公司的名字，所以不能当作候选标的。
GENERIC_TERMS = {
    "机器人", "谐波", "减速器", "伺服", "具身",
    "半导体", "算力", "芯片", "GPU", "CPU", "AI芯片",
    "光模块", "CPO", "光芯片", "光引擎", "硅光",
    "AI应用", "AI Agent", "人工智能", "大模型",
    "量子", "量子通信", "量子计算", "量子加密",
}


def find_keyword_candidates(themes: list, watchlist_with_names: list) -> dict:
    """
    关键词反向匹配：找出"关键词库里有但 watchlist 里没有"的公司名关键词。

    小白讲解：关键词库里列了很多公司名简称（如"海光"、"寒武纪"、"中际"），
    如果 watchlist 里没有包含这些简称的标的，就说明这些公司还没被我们覆盖。
    把它们收集起来作为"潜在候选关键词"，提示用户后续可以从外部数据源
    补全这些公司的完整代码。

    参数：
        themes: 主题 key 列表
        watchlist_with_names: watchlist 标的列表，每条有 ts_code/name/sector/market

    返回：
        dict：{theme_key: [keyword1, keyword2, ...]}，按主题分组的关键词列表
    """
    result = {}

    for theme_key in themes:
        theme_config = THEME_KEYWORDS.get(theme_key)
        if not theme_config:
            continue

        missing_keywords = []
        for keyword in theme_config["keywords"]:
            # 跳过通用词（行业概念词，不是公司名）
            if keyword in GENERIC_TERMS:
                continue

            # 检查这个关键词是否已经在 watchlist 的某个标的名中出现
            in_watchlist = any(
                keyword in wl["name"] or keyword in wl["ts_code"]
                for wl in watchlist_with_names
            )

            # 如果不在 watchlist 里，就是潜在候选
            if not in_watchlist:
                missing_keywords.append(keyword)

        if missing_keywords:
            result[theme_key] = missing_keywords

    return result


def determine_market(ts_code: str) -> str:
    """
    根据代码判断市场。

    小白讲解：看股票代码的格式就知道它在哪个市场。
    .SH 结尾是沪市，.SZ 是深市，.HK 是港股，纯字母是美股。

    参数：
        ts_code: 股票代码

    返回：
        "A" / "H" / "US" / "其他"
    """
    if ts_code.endswith(".SH") or ts_code.endswith(".SZ"):
        return "A"
    if ts_code.endswith(".HK"):
        return "H"
    if re.match(r"^[A-Z]+$", ts_code):
        return "US"
    return "其他"


# ============================================================
# 写入 discovery_candidate 表
# ============================================================

def ensure_discovery_tables(conn):
    """
    确保 discovery_candidate 等表存在。

    小白讲解：在写数据之前，先检查这些表建了没有，
    没建的话就建一下。
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS discovery_candidate (
            ticker TEXT NOT NULL,
            name TEXT,
            market TEXT,
            sector TEXT,
            discovery_method TEXT NOT NULL,
            hit_methods INTEGER DEFAULT 1,
            discovery_date TEXT NOT NULL,
            raw_source TEXT,
            added_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(ticker, discovery_method, discovery_date)
        );

        CREATE TABLE IF NOT EXISTS discovery_proposal (
            proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            name TEXT,
            market TEXT,
            sector TEXT,
            composite_score REAL,
            score_card_json TEXT,
            discovery_evidence_json TEXT,
            status TEXT DEFAULT 'pending_approval',
            approved_by TEXT,
            approved_at TEXT,
            reason TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(ticker)
        );

        CREATE TABLE IF NOT EXISTS value_score_snapshot (
            ticker TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            fundamental_quality REAL,
            valuation_position REAL,
            technical_momentum REAL,
            theme_relevance REAL,
            industry_position REAL,
            composite_score REAL,
            red_flags_json TEXT,
            score_detail_json TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            PRIMARY KEY(ticker, snapshot_date)
        );
    """)
    conn.commit()


def write_candidates(conn, candidates: list, discovery_date: str) -> int:
    """
    将发现的候选标的写入 discovery_candidate 表。

    小白讲解：把新发现的股票记到候选表里。
    如果同一只股票同一天已经记过了，就更新 hit_methods。

    参数：
        conn: 数据库连接
        candidates: 候选标的列表
        discovery_date: 发现日期

    返回：
        写入的记录数
    """
    written = 0
    for c in candidates:
        try:
            conn.execute("""
                INSERT INTO discovery_candidate
                    (ticker, name, market, sector, discovery_method, hit_methods,
                     discovery_date, raw_source)
                VALUES (?, ?, ?, ?, 'theme_extension', 1, ?, ?)
                ON CONFLICT(ticker, discovery_method, discovery_date)
                DO UPDATE SET hit_methods = hit_methods + 1
            """, (
                c["ticker"], c["name"], c["market"], c["sector"],
                discovery_date, c.get("raw_source", "theme_extension scan")
            ))
            written += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    return written


# ============================================================
# 主流程
# ============================================================

def run_scan(dry_run: bool = False) -> dict:
    """
    主题扩展扫描主流程。

    小白讲解：这是整个管道的"总指挥"函数，按以下 6 步执行：
    1. 读 5 大主题定义
    2. 读已有标的清单（带名称和 sector）
    3. 从数据库取所有标的（如果数据库有的话）
    4. 主题匹配：
       - 4a：数据库标的做主题匹配，找"主题内但未在 watchlist"的真实标的
       - 4b：关键词反向匹配，找"关键词库里有但 watchlist 里没有"的公司名关键词
    5. 写入 discovery_candidate 表（仅 4a 的真实候选）
    6. 输出扫描摘要

    参数：
        dry_run: 如果为 True，只输出结果不写数据库

    返回：
        dict：扫描结果摘要
    """
    print("=" * 60)
    print("主题扩展扫描管道（theme_extension pipeline）")
    print("=" * 60)

    # 步骤 1：读取主题定义
    themes = parse_sector_priority_map(SECTOR_MAP_PATH)
    print(f"\n[1/6] 读取到 {len(themes)} 个主题：")
    for t in themes:
        print(f"       - {t} ({THEME_KEYWORDS.get(t, {}).get('name', '未知')})")

    # 步骤 2：读取已有标的（带名称和 sector）
    existing_codes = parse_watchlist_registry(WATCHLIST_PATH)
    watchlist_with_names = parse_watchlist_with_names(WATCHLIST_PATH)
    print(f"\n[2/6] watchlist_registry 解析出 {len(watchlist_with_names)} 个标的"
          f"（{len(existing_codes)} 个代码）")

    # 步骤 3：从数据库获取所有标的
    conn = get_db_connection()
    all_stocks = get_all_stocks_with_sector(conn)
    print(f"\n[3/6] 数据库 stock_pool 中有 {len(all_stocks)} 个活跃标的")

    # 获取股票名称
    all_tickers = [s["ts_code"] for s in all_stocks]
    name_map = get_stock_names(conn, all_tickers)

    # 步骤 4：主题匹配
    print(f"\n[4/6] 开始主题匹配...")
    matched = {}  # {ticker: {theme, name, market, sector, pool_type}}

    # 4a. 从数据库标的中匹配（找真实的新候选）
    for stock in all_stocks:
        ts_code = stock["ts_code"]
        sector = stock.get("sector", "")
        stock_name = name_map.get(ts_code, ts_code)

        # 如果已经在 watchlist 里，跳过
        if ts_code in existing_codes:
            continue

        # 匹配主题
        matched_theme = match_stock_to_theme(ts_code, sector, stock_name, themes)
        if matched_theme:
            matched[ts_code] = {
                "ticker": ts_code,
                "name": stock_name,
                "market": determine_market(ts_code),
                "sector": matched_theme,
                "pool_type": stock.get("pool_type", ""),
                "raw_source": f"数据库匹配：{THEME_KEYWORDS[matched_theme]['name']}",
            }

    print(f"       [4a] 数据库匹配到 {len(matched)} 个主题内但未在 watchlist 中的标的")

    # 4b. 关键词反向匹配：找"关键词库里有但 watchlist 里没有"的公司名关键词
    # 小白讲解：关键词库里有很多公司名简称（如"海光"、"寒武纪"），
    # 如果 watchlist 里没有包含这些简称的标的，就说明这些公司还没被覆盖，
    # 可以作为"潜在候选"提示给用户，等后续从外部数据源补全代码。
    keyword_candidates = find_keyword_candidates(themes, watchlist_with_names)
    total_kw_candidates = sum(len(v) for v in keyword_candidates.values())
    print(f"       [4b] 关键词反向匹配发现 {total_kw_candidates} 个潜在候选关键词"
          f"（分布在 {len(keyword_candidates)} 个主题，待外部数据补全代码）")

    # 按主题分组显示
    by_theme = {}
    for c in matched.values():
        by_theme.setdefault(c["sector"], []).append(c)

    for theme_key in themes:
        theme_name = THEME_KEYWORDS.get(theme_key, {}).get("name", theme_key)
        count = len(by_theme.get(theme_key, []))
        kw_count = len(keyword_candidates.get(theme_key, []))
        print(f"       - {theme_name}: {count} 个真实候选 / {kw_count} 个潜在关键词")

    # 步骤 5：写入数据库
    discovery_date = datetime.now().strftime("%Y-%m-%d")

    if dry_run:
        print(f"\n[5/6] [dry-run] 不写入数据库，跳过 {len(matched)} 条记录")
    else:
        ensure_discovery_tables(conn)
        written = write_candidates(conn, list(matched.values()), discovery_date)
        print(f"\n[5/6] 写入 discovery_candidate 表：{written} 条记录")

    conn.close()

    # 输出真实候选清单
    if matched:
        print("\n" + "-" * 60)
        print("发现的新候选标的清单（真实候选）：")
        print("-" * 60)
        for theme_key in themes:
            theme_name = THEME_KEYWORDS.get(theme_key, {}).get("name", theme_key)
            candidates = by_theme.get(theme_key, [])
            if candidates:
                print(f"\n  【{theme_name}】({len(candidates)} 个)")
                for c in candidates:
                    print(f"    {c['ticker']:>12s}  {c['name']:<16s}  [{c['market']}]")

    # 输出潜在候选关键词清单
    if keyword_candidates:
        print("\n" + "-" * 60)
        print("潜在候选关键词清单（待外部数据补全代码）：")
        print("-" * 60)
        for theme_key in themes:
            theme_name = THEME_KEYWORDS.get(theme_key, {}).get("name", theme_key)
            kws = keyword_candidates.get(theme_key, [])
            if kws:
                print(f"\n  【{theme_name}】({len(kws)} 个关键词)")
                # 每行显示 5 个关键词
                for i in range(0, len(kws), 5):
                    batch = kws[i:i+5]
                    print(f"    {', '.join(batch)}")

    # 结果摘要
    total_kw = sum(len(v) for v in keyword_candidates.values())
    summary = {
        "themes_scanned": len(themes),
        "existing_count": len(existing_codes),
        "db_stock_count": len(all_stocks),
        "new_candidates": len(matched),
        "keyword_candidates": total_kw,
        "by_theme": {
            THEME_KEYWORDS.get(k, {}).get("name", k): len(v)
            for k, v in by_theme.items()
        },
        "dry_run": dry_run,
        "discovery_date": discovery_date,
    }

    print(f"\n{'=' * 60}")
    print("扫描完成！")
    print(f"  主题数: {summary['themes_scanned']}")
    print(f"  已有标的: {summary['existing_count']}")
    print(f"  数据库标的: {summary['db_stock_count']}")
    print(f"  新发现候选（真实）: {summary['new_candidates']}")
    print(f"  潜在候选关键词: {summary['keyword_candidates']}")
    print(f"  模式: {'dry-run（不写入）' if dry_run else '正式（已写入数据库）'}")
    print("=" * 60)

    return summary


# ============================================================
# 命令行入口
# ============================================================

def main():
    """
    命令行入口函数。

    支持参数：
        --dry-run: 只扫描不写入数据库
        --force: 强制运行（忽略 self_discovery_enabled 门禁开关，用于开发验证）
    """
    parser = argparse.ArgumentParser(description="主题扩展扫描管道")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只扫描不写入数据库"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="强制运行（忽略 self_discovery_enabled 门禁开关，用于开发验证）"
    )
    args = parser.parse_args()

    # SPEC 2 AC-6：门禁开关 early-exit 检查
    # 小白讲解：如果"自主发现管线"门禁开关是关的，且没有加 --force，
    # 脚本就提前退出，不执行扫描。这是为了防止开发模式下意外触发扫描。
    if not args.force and not check_self_discovery_enabled():
        print("=" * 60)
        print("[early-exit] 自主发现管线门禁已禁用（self_discovery_enabled=False）")
        print("[early-exit] 扫描脚本未执行。")
        print("[early-exit] 如需手动验证管线，请加 --force 参数：")
        print(f"[early-exit]   python {Path(__file__).name} --force")
        print(f"[early-exit]   python {Path(__file__).name} --force --dry-run")
        print("[early-exit] 如需正式启用，请在 smr_guard.py 设置 self_discovery_enabled=True")
        print("=" * 60)
        return 0

    if args.force and not check_self_discovery_enabled():
        print("[提示] --force 模式：忽略 self_discovery_enabled=False 门禁，强制运行（开发验证用）")

    result = run_scan(dry_run=args.dry_run)

    # 退出码：0=成功，1=没有发现新候选（不是错误，只是提示）
    return 0


if __name__ == "__main__":
    sys.exit(main())
