#!/usr/bin/env python3
"""
产业链扩展扫描管道（supply_chain_extension pipeline）

功能：
    对每只种子标的，基于 5 大主题的供应链上下游关键词库，
    查找上游（原材料/核心零部件）和下游（系统集成/应用端）的标的，
    与 watchlist_registry.md 中的已有标的做差集，
    输出"供应链相关但未覆盖"的标的清单，写入 discovery_candidate 表。

小白讲解：
    这个脚本像"供应链侦探"——已知我们关注"中际旭创"（光模块），
    那它的上游有光芯片厂（如光迅），下游有数据中心设备厂（如浪潮）。
    我们把这些上下游公司找出来，看哪些还没被我们关注，记到候选表里。

输入：
    - sector_priority_map.md：5 大主题定义
    - watchlist_registry.md：已有标的清单
    - stock_pool_current 表：数据库中所有标的（如果有的话）
    - supply_chain_theme_templates.json：供应链模板（参考）

输出：
    - discovery_candidate 表：新发现的候选标的（discovery_method='supply_chain'）
    - 控制台日志：扫描结果摘要

用法：
    python 08_scripts/self_discovery/scan_supply_chain_extension.py
    python 08_scripts/self_discovery/scan_supply_chain_extension.py --dry-run   # 只看不写

安全约束：
    - 发现候选只写入 discovery_candidate 表
    - 永远不会自动写入 stock_pool 表
    - 需要人工批准后才能入池
"""

import argparse
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

# 把同目录加到 sys.path，方便 import theme_extension 的公共函数
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 复用 theme_extension 的公共函数（避免代码重复）
from scan_theme_extension import (  # noqa: E402
    check_self_discovery_enabled,
    determine_market,
    ensure_discovery_tables,
    get_all_stocks_with_sector,
    get_db_connection,
    get_stock_names,
    parse_watchlist_registry,
    parse_watchlist_with_names,
    write_candidates as _write_candidates_theme,
)


# ============================================================
# 5 大主题的供应链上下游关键词库
#
# 小白讲解：每个主题都有"上游"和"下游"两部分公司名关键词。
# 上游 = 提供原材料或核心零部件的公司（如光芯片厂给光模块厂供货）
# 下游 = 做系统集成或应用的公司（如用光模块建数据中心的公司）
# 这些关键词用于匹配数据库标的，找出供应链上的相关公司。
# ============================================================

SUPPLY_CHAIN_KEYWORDS = {
    "embodied_ai": {
        "name": "具身智能/机器人",
        "upstream": {
            "description": "上游：减速器、伺服电机、传感器、控制器",
            "keywords": [
                "绿的", "双环", "中大力德", "来福", "汉宇",
                "汇川", "英威腾", "鸣志", "步科",
                "奥比", "柯力", "汉威", "苏奥",
                "埃斯顿", "新时达", "华中",
            ],
        },
        "downstream": {
            "description": "下游：机器人整机、自动化产线",
            "keywords": [
                "埃斯顿", "新时达", "华中数控", "拓斯达",
                "机器人", "优必选", "智元", "宇树",
                "特斯拉", "博实", "晶品",
            ],
        },
    },
    "semiconductor_compute": {
        "name": "半导体/算力芯片",
        "upstream": {
            "description": "上游：硅片、光刻胶、EDA、半导体设备",
            "keywords": [
                "沪硅", "中环", "立昂微", "神工",
                "华大九天", "概伦", "广立微",
                "北方华创", "中微", "长川", "华峰测控",
                "盛美", "至纯", "芯源微",
            ],
        },
        "downstream": {
            "description": "下游：服务器、数据中心、云计算",
            "keywords": [
                "浪潮", "中科曙光", "紫光", "工业富联",
                "联想", "新华三", "宝信",
                "数据港", "光环新网", "万国数据",
                "秦淮", "润泽",
            ],
        },
    },
    "semiconductor_photonics": {
        "name": "光模块/CPO",
        "upstream": {
            "description": "上游：光芯片、光器件、硅光芯片",
            "keywords": [
                "光迅", "源杰", "仕佳", "长光华芯",
                "永鼎", "通宇", "太辰光", "华工科技",
                "天孚", "新易盛", "光库",
                "博创科技", "铭普光磁", "剑桥科技",
            ],
        },
        "downstream": {
            "description": "下游：数通设备、AI 服务器",
            "keywords": [
                "浪潮", "中兴", "紫光", "锐捷",
                "菲菱科思", "工业富联",
                "曙光数创", "英维克", "高澜",
            ],
        },
    },
    "ai_agent": {
        "name": "AI Agent/应用",
        "upstream": {
            "description": "上游：算力基础设施、大模型平台",
            "keywords": [
                "海光", "寒武纪", "百度", "阿里",
                "腾讯", "字节", "商汤", "旷视",
                "科大讯飞", "智谱",
            ],
        },
        "downstream": {
            "description": "下游：行业应用、企业服务",
            "keywords": [
                "金山", "泛微", "致远", "万兴",
                "福昕", "用友", "金蝶",
                "恒生电子", "同花顺", "顶点",
                "卫宁", "创业慧康",
            ],
        },
    },
    "quantum": {
        "name": "量子/前沿科学",
        "upstream": {
            "description": "上游：量子器件、低温设备",
            "keywords": [
                "国盾", "本源", "国仪",
                "中科大国创", "光迅",
                "亨通", "中天", "神州",
            ],
        },
        "downstream": {
            "description": "下游：量子通信网络、量子加密应用",
            "keywords": [
                "神州信息", "迪普", "卫士通",
                "格尔", "飞天", "蓝盾",
                "科华", "铜牛",
            ],
        },
    },
}

# 通用词集合：不会作为候选标的的行业概念词
GENERIC_TERMS = {
    "机器人", "光模块", "芯片", "半导体", "算力", "量子",
    "光芯片", "光引擎", "硅光", "CPO", "GPU", "CPU",
}


# ============================================================
# 供应链匹配逻辑
# ============================================================

def match_stock_to_supply_chain(ts_code: str, sector: str, stock_name: str, themes: list) -> list:
    """
    判断一只股票在供应链上的位置（上游/下游）。

    小白讲解：看这只股票的名字和赛道，
    如果它的名字包含了某个主题"上游关键词"或"下游关键词"，
    就记录下来它属于哪个主题的哪个位置。

    参数：
        ts_code: 股票代码
        sector: 数据库里的 sector 标签
        stock_name: 股票名称
        themes: 要匹配的主题 key 列表

    返回：
        list：匹配结果列表，每条是
              {"theme": ..., "position": "upstream"/"downstream", "keyword": ...}
        没匹配到返回空列表
    """
    text = f"{sector} {stock_name} {ts_code}"
    matches = []

    for theme_key in themes:
        sc_config = SUPPLY_CHAIN_KEYWORDS.get(theme_key)
        if not sc_config:
            continue

        # 检查上游关键词
        for keyword in sc_config["upstream"]["keywords"]:
            if keyword in text:
                matches.append({
                    "theme": theme_key,
                    "position": "upstream",
                    "keyword": keyword,
                })
                break  # 同一主题同一位置只记一次

        # 检查下游关键词
        for keyword in sc_config["downstream"]["keywords"]:
            if keyword in text:
                matches.append({
                    "theme": theme_key,
                    "position": "downstream",
                    "keyword": keyword,
                })
                break

    return matches


def find_supply_chain_keyword_candidates(themes: list, watchlist_with_names: list) -> dict:
    """
    关键词反向匹配：找出"供应链关键词库里有但 watchlist 里没有"的公司名关键词。

    小白讲解：和 theme_extension 的 find_keyword_candidates 类似，
    但这里分上游和下游两个方向。
    如果某个上游/下游公司名关键词不在 watchlist 里，
    就把它作为"潜在候选"记录下来。

    参数：
        themes: 主题 key 列表
        watchlist_with_names: watchlist 标的列表

    返回：
        dict：{theme_key: {"upstream": [...], "downstream": [...]}}
    """
    result = {}

    for theme_key in themes:
        sc_config = SUPPLY_CHAIN_KEYWORDS.get(theme_key)
        if not sc_config:
            continue

        theme_result = {"upstream": [], "downstream": []}

        for position in ("upstream", "downstream"):
            for keyword in sc_config[position]["keywords"]:
                # 跳过通用词
                if keyword in GENERIC_TERMS:
                    continue

                # 检查关键词是否已在 watchlist 标的名中
                in_watchlist = any(
                    keyword in wl["name"] or keyword in wl["ts_code"]
                    for wl in watchlist_with_names
                )

                if not in_watchlist:
                    theme_result[position].append(keyword)

        if theme_result["upstream"] or theme_result["downstream"]:
            result[theme_key] = theme_result

    return result


# ============================================================
# 写入 discovery_candidate 表
# ============================================================

def write_supply_chain_candidates(conn, candidates: list, discovery_date: str) -> int:
    """
    将供应链发现的候选标的写入 discovery_candidate 表。

    小白讲解：和 theme_extension 的 write_candidates 类似，
    但 discovery_method 标记为 'supply_chain'。

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
                VALUES (?, ?, ?, ?, 'supply_chain', 1, ?, ?)
                ON CONFLICT(ticker, discovery_method, discovery_date)
                DO UPDATE SET hit_methods = hit_methods + 1
            """, (
                c["ticker"], c["name"], c["market"], c["sector"],
                discovery_date, c.get("raw_source", "supply_chain scan")
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
    产业链扩展扫描主流程。

    小白讲解：这是供应链管道的"总指挥"函数，按以下 6 步执行：
    1. 读 5 大主题定义
    2. 读已有标的清单（带名称和 sector）
    3. 从数据库取所有标的（如果数据库有的话）
    4. 供应链匹配：
       - 4a：数据库标的做上下游关键词匹配，找"供应链相关但未在 watchlist"的真实标的
       - 4b：关键词反向匹配，找"供应链关键词库里有但 watchlist 里没有"的公司名关键词
    5. 写入 discovery_candidate 表（仅 4a 的真实候选）
    6. 输出扫描摘要

    参数：
        dry_run: 如果为 True，只输出结果不写数据库

    返回：
        dict：扫描结果摘要
    """
    print("=" * 60)
    print("产业链扩展扫描管道（supply_chain_extension pipeline）")
    print("=" * 60)

    # 步骤 1：读取主题定义（复用 theme_extension 的函数）
    # 直接用 SUPPLY_CHAIN_KEYWORDS 的 key 作为主题列表
    themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
    print(f"\n[1/6] 读取到 {len(themes)} 个主题的供应链定义：")
    for t in themes:
        sc = SUPPLY_CHAIN_KEYWORDS[t]
        up_count = len(sc["upstream"]["keywords"])
        down_count = len(sc["downstream"]["keywords"])
        print(f"       - {t} ({sc['name']}): 上游 {up_count} 词 / 下游 {down_count} 词")

    # 步骤 2：读取已有标的
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

    # 步骤 4：供应链匹配
    print(f"\n[4/6] 开始供应链匹配...")
    matched = {}  # {ticker: {name, market, sector, position, raw_source}}

    # 4a. 从数据库标的中匹配
    for stock in all_stocks:
        ts_code = stock["ts_code"]
        sector = stock.get("sector", "")
        stock_name = name_map.get(ts_code, ts_code)

        # 如果已经在 watchlist 里，跳过
        if ts_code in existing_codes:
            continue

        # 匹配供应链位置
        sc_matches = match_stock_to_supply_chain(ts_code, sector, stock_name, themes)
        if sc_matches:
            # 取第一个匹配（一只股票可能匹配多个主题位置，取优先的）
            first = sc_matches[0]
            matched[ts_code] = {
                "ticker": ts_code,
                "name": stock_name,
                "market": determine_market(ts_code),
                "sector": first["theme"],
                "raw_source": f"供应链匹配：{first['position']}（{first['keyword']}）",
            }

    print(f"       [4a] 数据库匹配到 {len(matched)} 个供应链相关但未在 watchlist 中的标的")

    # 4b. 关键词反向匹配
    keyword_candidates = find_supply_chain_keyword_candidates(themes, watchlist_with_names)
    total_up = sum(len(v.get("upstream", [])) for v in keyword_candidates.values())
    total_down = sum(len(v.get("downstream", [])) for v in keyword_candidates.values())
    total_kw = total_up + total_down
    print(f"       [4b] 关键词反向匹配发现 {total_kw} 个潜在候选关键词"
          f"（上游 {total_up} / 下游 {total_down}，待外部数据补全代码）")

    # 按主题分组显示
    for theme_key in themes:
        sc_name = SUPPLY_CHAIN_KEYWORDS.get(theme_key, {}).get("name", theme_key)
        real_count = sum(1 for c in matched.values() if c["sector"] == theme_key)
        up_kw = len(keyword_candidates.get(theme_key, {}).get("upstream", []))
        down_kw = len(keyword_candidates.get(theme_key, {}).get("downstream", []))
        print(f"       - {sc_name}: {real_count} 个真实候选 / 上游 {up_kw} 词 / 下游 {down_kw} 词")

    # 步骤 5：写入数据库
    discovery_date = datetime.now().strftime("%Y-%m-%d")

    if dry_run:
        print(f"\n[5/6] [dry-run] 不写入数据库，跳过 {len(matched)} 条记录")
    else:
        ensure_discovery_tables(conn)
        written = write_supply_chain_candidates(conn, list(matched.values()), discovery_date)
        print(f"\n[5/6] 写入 discovery_candidate 表：{written} 条记录")

    conn.close()

    # 输出真实候选清单
    if matched:
        print("\n" + "-" * 60)
        print("发现的新候选标的清单（真实候选）：")
        print("-" * 60)
        for theme_key in themes:
            sc_name = SUPPLY_CHAIN_KEYWORDS.get(theme_key, {}).get("name", theme_key)
            candidates = [c for c in matched.values() if c["sector"] == theme_key]
            if candidates:
                print(f"\n  【{sc_name}】({len(candidates)} 个)")
                for c in candidates:
                    print(f"    {c['ticker']:>12s}  {c['name']:<16s}  [{c['market']}]  {c['raw_source']}")

    # 输出潜在候选关键词清单
    if keyword_candidates:
        print("\n" + "-" * 60)
        print("潜在候选关键词清单（待外部数据补全代码）：")
        print("-" * 60)
        for theme_key in themes:
            sc_name = SUPPLY_CHAIN_KEYWORDS.get(theme_key, {}).get("name", theme_key)
            kc = keyword_candidates.get(theme_key)
            if kc and (kc["upstream"] or kc["downstream"]):
                print(f"\n  【{sc_name}】")
                if kc["upstream"]:
                    print(f"    上游 ({len(kc['upstream'])} 个): {', '.join(kc['upstream'])}")
                if kc["downstream"]:
                    print(f"    下游 ({len(kc['downstream'])} 个): {', '.join(kc['downstream'])}")

    # 结果摘要
    summary = {
        "themes_scanned": len(themes),
        "existing_count": len(existing_codes),
        "db_stock_count": len(all_stocks),
        "new_candidates": len(matched),
        "keyword_candidates_upstream": total_up,
        "keyword_candidates_downstream": total_down,
        "dry_run": dry_run,
        "discovery_date": discovery_date,
    }

    print(f"\n{'=' * 60}")
    print("扫描完成！")
    print(f"  主题数: {summary['themes_scanned']}")
    print(f"  已有标的: {summary['existing_count']}")
    print(f"  数据库标的: {summary['db_stock_count']}")
    print(f"  新发现候选（真实）: {summary['new_candidates']}")
    print(f"  潜在候选关键词: 上游 {total_up} / 下游 {total_down}")
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
    parser = argparse.ArgumentParser(description="产业链扩展扫描管道")
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
    if not args.force and not check_self_discovery_enabled():
        print("=" * 60)
        print("[early-exit] 自主发现管线门禁已禁用（self_discovery_enabled=False）")
        print("[early-exit] 供应链扩展扫描未执行。")
        print("[early-exit] 如需手动验证管线，请加 --force 参数：")
        print(f"[early-exit]   python {Path(__file__).name} --force")
        print(f"[early-exit]   python {Path(__file__).name} --force --dry-run")
        print("[early-exit] 如需正式启用，请在 smr_guard.py 设置 self_discovery_enabled=True")
        print("=" * 60)
        return 0

    if args.force and not check_self_discovery_enabled():
        print("[提示] --force 模式：忽略 self_discovery_enabled=False 门禁，强制运行（开发验证用）")

    run_scan(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
