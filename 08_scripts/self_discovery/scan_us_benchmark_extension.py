#!/usr/bin/env python3
"""
美股对标映射扩展扫描管道（us_benchmark_extension pipeline）

功能：
    基于 sector_priority_map.md 的"美股对标映射"，
    对每只美股对标，查找 A股/H股 中与其同行业/同业务的公司，
    与 watchlist_registry.md 中的已有标的做差集，
    输出"美股对标的 A股映射"候选，写入 discovery_candidate 表。

小白讲解：
    这个脚本像"翻译官"——美股有英伟达（NVDA），我们找 A股里和它做类似事情的
    公司（如海光信息、寒武纪）。美股有特斯拉（TSLA），我们找 A股里做机器人
    零部件的公司（如拓普集团、绿的谐波）。找到后记到候选表里。

输入：
    - sector_priority_map.md：美股对标映射表
    - watchlist_registry.md：已有标的清单
    - stock_pool_current 表：数据库中所有标的（如果有的话）

输出：
    - discovery_candidate 表：新发现的候选标的（discovery_method='us_benchmark'）
    - 控制台日志：扫描结果摘要

用法：
    python 08_scripts/self_discovery/scan_us_benchmark_extension.py
    python 08_scripts/self_discovery/scan_us_benchmark_extension.py --dry-run   # 只看不写

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "01_data" / "db" / "smr.db"
SECTOR_MAP_PATH = PROJECT_ROOT / "00_control" / "sector_priority_map.md"
WATCHLIST_PATH = PROJECT_ROOT / "00_control" / "watchlist_registry.md"

# 把同目录加到 sys.path，方便 import 公共函数
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scan_theme_extension import (  # noqa: E402
    check_self_discovery_enabled,
    determine_market,
    ensure_discovery_tables,
    get_all_stocks_with_sector,
    get_db_connection,
    get_stock_names,
    parse_watchlist_registry,
    parse_watchlist_with_names,
)


# ============================================================
# 美股对标 → A股/H股映射关键词库
#
# 小白讲解：每只美股对标都有对应的 A股/H股"相似公司"关键词。
# 这些关键词是公司名简称，用于匹配数据库标的。
# 映射类型说明：
#   - 业务对标：做类似业务的公司（如 NVDA ↔ 海光信息）
#   - 供应链对标：在同一个供应链上的公司（如 NVDA ↔ 中际旭创）
#   - 估值锚对标：估值可以参考的公司（如 IONQ ↔ 国盾量子）
# ============================================================

US_BENCHMARK_MAPPING = {
    # ===== 半导体/算力芯片 =====
    "NVDA": {
        "name": "英伟达",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "GPU/AI 加速器设计",
        "a_h_keywords": ["海光", "寒武纪", "景嘉微", "芯原"],
    },
    "AMD": {
        "name": "超微半导体",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "CPU/GPU 设计",
        "a_h_keywords": ["海光", "寒武纪", "兆易"],
    },
    "INTC": {
        "name": "英特尔",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "CPU/晶圆制造",
        "a_h_keywords": ["中芯", "华虹", "海光"],
    },
    "AVGO": {
        "name": "博通",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "网络芯片/定制 ASIC",
        "a_h_keywords": ["澜起", "紫光", "韦尔"],
    },
    "MU": {
        "name": "美光",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "存储芯片（DRAM/NAND）",
        "a_h_keywords": ["兆易", "澜起", "深科技"],
    },
    "SNPS": {
        "name": "Synopsys",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "EDA 工具",
        "a_h_keywords": ["华大九天", "概伦", "广立微"],
    },
    "CDNS": {
        "name": "Cadence",
        "sector": "semiconductor_compute",
        "mapping_type": "业务对标",
        "business": "EDA 工具",
        "a_h_keywords": ["华大九天", "概伦", "广立微"],
    },

    # ===== 光模块/CPO =====
    "LITE": {
        "name": "Lumentum",
        "sector": "semiconductor_photonics",
        "mapping_type": "业务对标",
        "business": "光芯片/光器件",
        "a_h_keywords": ["光迅", "源杰", "仕佳", "长光华芯"],
    },
    "MRVL": {
        "name": "Marvell",
        "sector": "semiconductor_photonics",
        "mapping_type": "业务对标",
        "business": "网络芯片/光互连",
        "a_h_keywords": ["中际", "新易盛", "光迅"],
    },
    "COHR": {
        "name": "Coherent",
        "sector": "semiconductor_photonics",
        "mapping_type": "业务对标",
        "business": "光器件/激光器",
        "a_h_keywords": ["光迅", "华工科技", "光库"],
    },
    "VRT": {
        "name": "Vertiv",
        "sector": "semiconductor_photonics",
        "mapping_type": "供应链对标",
        "business": "数据中心制冷/电源",
        "a_h_keywords": ["英维克", "曙光数创", "高澜"],
    },

    # ===== 具身智能/机器人 =====
    "TSLA": {
        "name": "特斯拉",
        "sector": "embodied_ai",
        "mapping_type": "业务对标",
        "business": "电动车+人形机器人",
        "a_h_keywords": ["拓普", "三花", "绿的", "鸣志", "汇川"],
    },

    # ===== AI Agent/应用 =====
    "CRM": {
        "name": "Salesforce",
        "sector": "ai_agent",
        "mapping_type": "业务对标",
        "business": "CRM SaaS/AI 应用",
        "a_h_keywords": ["金山", "用友", "金蝶", "泛微"],
    },
    "NOW": {
        "name": "ServiceNow",
        "sector": "ai_agent",
        "mapping_type": "业务对标",
        "business": "IT 服务管理 SaaS",
        "a_h_keywords": ["金山", "致远", "泛微"],
    },
    "MSFT": {
        "name": "微软",
        "sector": "ai_agent",
        "mapping_type": "业务对标",
        "business": "云+办公+AI 平台",
        "a_h_keywords": ["金山", "科大讯飞", "用友"],
    },

    # ===== 量子 =====
    "IONQ": {
        "name": "IonQ",
        "sector": "quantum",
        "mapping_type": "估值锚对标",
        "business": "离子阱量子计算",
        "a_h_keywords": ["国盾", "本源", "国仪"],
    },
    "RGTI": {
        "name": "Rigetti",
        "sector": "quantum",
        "mapping_type": "估值锚对标",
        "business": "超导量子计算",
        "a_h_keywords": ["国盾", "本源", "国仪"],
    },
    "QBTS": {
        "name": "D-Wave",
        "sector": "quantum",
        "mapping_type": "估值锚对标",
        "business": "量子退火",
        "a_h_keywords": ["国盾", "本源", "国仪"],
    },
}

# 通用词集合
GENERIC_TERMS = {
    "机器人", "光模块", "芯片", "半导体", "算力", "量子",
    "光芯片", "光引擎", "硅光", "CPO", "GPU", "CPU", "AI芯片",
}


# ============================================================
# 美股对标映射匹配逻辑
# ============================================================

def match_stock_to_us_benchmark(ts_code: str, stock_name: str) -> list:
    """
    判断一只 A股/H股标的与哪些美股对标相关。

    小白讲解：看这只 A股的名字，如果它包含了某个美股对标的"A股映射关键词"，
    就记录下来它和哪只美股对标相关。

    参数：
        ts_code: 股票代码
        stock_name: 股票名称

    返回：
        list：匹配结果列表，每条是
              {"us_symbol": ..., "us_name": ..., "sector": ..., "keyword": ..., "mapping_type": ...}
        没匹配到返回空列表
    """
    text = f"{stock_name} {ts_code}"
    matches = []

    for us_symbol, config in US_BENCHMARK_MAPPING.items():
        for keyword in config["a_h_keywords"]:
            if keyword in text:
                matches.append({
                    "us_symbol": us_symbol,
                    "us_name": config["name"],
                    "sector": config["sector"],
                    "keyword": keyword,
                    "mapping_type": config["mapping_type"],
                })
                break  # 同一美股对标只记一次

    return matches


def find_benchmark_keyword_candidates(watchlist_with_names: list) -> dict:
    """
    关键词反向匹配：找出"美股映射关键词里有但 watchlist 里没有"的公司名关键词。

    小白讲解：对每只美股对标，它的映射关键词库里有一些 A股公司名简称，
    如果这些简称不在 watchlist 里，就说明这些 A股公司还没被我们覆盖，
    可以作为"美股对标的 A股映射候选"。

    参数：
        watchlist_with_names: watchlist 标的列表

    返回：
        dict：{us_symbol: {"us_name": ..., "missing_keywords": [...]}}
    """
    result = {}

    for us_symbol, config in US_BENCHMARK_MAPPING.items():
        missing = []
        for keyword in config["a_h_keywords"]:
            # 跳过通用词
            if keyword in GENERIC_TERMS:
                continue

            # 检查关键词是否已在 watchlist 标的名中
            in_watchlist = any(
                keyword in wl["name"] or keyword in wl["ts_code"]
                for wl in watchlist_with_names
            )

            if not in_watchlist:
                missing.append(keyword)

        if missing:
            result[us_symbol] = {
                "us_name": config["name"],
                "sector": config["sector"],
                "mapping_type": config["mapping_type"],
                "missing_keywords": missing,
            }

    return result


# ============================================================
# 写入 discovery_candidate 表
# ============================================================

def write_benchmark_candidates(conn, candidates: list, discovery_date: str) -> int:
    """
    将美股对标映射发现的候选标的写入 discovery_candidate 表。

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
                VALUES (?, ?, ?, ?, 'us_benchmark', 1, ?, ?)
                ON CONFLICT(ticker, discovery_method, discovery_date)
                DO UPDATE SET hit_methods = hit_methods + 1
            """, (
                c["ticker"], c["name"], c["market"], c["sector"],
                discovery_date, c.get("raw_source", "us_benchmark scan")
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
    美股对标映射扩展扫描主流程。

    小白讲解：这是美股对标管道的"总指挥"函数，按以下 6 步执行：
    1. 显示美股对标映射库
    2. 读已有标的清单
    3. 从数据库取所有 A股/H股标的
    4. 美股映射匹配：
       - 4a：数据库标的做映射关键词匹配，找"与美股对标相关但未在 watchlist"的真实标的
       - 4b：关键词反向匹配，找"映射关键词里有但 watchlist 里没有"的公司名关键词
    5. 写入 discovery_candidate 表
    6. 输出扫描摘要

    参数：
        dry_run: 如果为 True，只输出结果不写数据库

    返回：
        dict：扫描结果摘要
    """
    print("=" * 60)
    print("美股对标映射扩展扫描管道（us_benchmark_extension pipeline）")
    print("=" * 60)

    # 步骤 1：显示美股对标映射库
    print(f"\n[1/6] 美股对标映射库：{len(US_BENCHMARK_MAPPING)} 只美股")
    # 按行业分组显示
    by_sector = {}
    for symbol, config in US_BENCHMARK_MAPPING.items():
        by_sector.setdefault(config["sector"], []).append(symbol)
    for sector, symbols in by_sector.items():
        print(f"       - {sector}: {', '.join(symbols)}")

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

    # 步骤 4：美股映射匹配
    print(f"\n[4/6] 开始美股对标映射匹配...")
    matched = {}  # {ticker: {name, market, sector, raw_source}}

    # 4a. 从数据库标的中匹配（只匹配 A股/H股，不匹配美股本身）
    for stock in all_stocks:
        ts_code = stock["ts_code"]
        stock_name = name_map.get(ts_code, ts_code)

        # 如果已经在 watchlist 里，跳过
        if ts_code in existing_codes:
            continue

        # 美股本身不参与匹配（只找 A股/H股映射）
        if determine_market(ts_code) == "US":
            continue

        # 匹配美股对标
        bm_matches = match_stock_to_us_benchmark(ts_code, stock_name)
        if bm_matches:
            first = bm_matches[0]
            matched[ts_code] = {
                "ticker": ts_code,
                "name": stock_name,
                "market": determine_market(ts_code),
                "sector": first["sector"],
                "raw_source": f"美股对标：{first['us_symbol']}（{first['us_name']}）"
                              f"-{first['mapping_type']}",
            }

    print(f"       [4a] 数据库匹配到 {len(matched)} 个与美股对标相关但未在 watchlist 中的标的")

    # 4b. 关键词反向匹配
    keyword_candidates = find_benchmark_keyword_candidates(watchlist_with_names)
    total_kw = sum(len(v["missing_keywords"]) for v in keyword_candidates.values())
    print(f"       [4b] 关键词反向匹配发现 {total_kw} 个潜在候选关键词"
          f"（分布在 {len(keyword_candidates)} 只美股对标，待外部数据补全代码）")

    # 按美股对标显示
    for us_symbol, config in US_BENCHMARK_MAPPING.items():
        kc = keyword_candidates.get(us_symbol)
        missing_count = len(kc["missing_keywords"]) if kc else 0
        if missing_count > 0:
            print(f"       - {us_symbol} ({config['name']}): {missing_count} 个潜在候选")

    # 步骤 5：写入数据库
    discovery_date = datetime.now().strftime("%Y-%m-%d")

    if dry_run:
        print(f"\n[5/6] [dry-run] 不写入数据库，跳过 {len(matched)} 条记录")
    else:
        ensure_discovery_tables(conn)
        written = write_benchmark_candidates(conn, list(matched.values()), discovery_date)
        print(f"\n[5/6] 写入 discovery_candidate 表：{written} 条记录")

    conn.close()

    # 输出真实候选清单
    if matched:
        print("\n" + "-" * 60)
        print("发现的新候选标的清单（真实候选）：")
        print("-" * 60)
        for us_symbol, config in US_BENCHMARK_MAPPING.items():
            candidates = [c for c in matched.values() if us_symbol in c.get("raw_source", "")]
            if candidates:
                print(f"\n  【{us_symbol} - {config['name']}】({len(candidates)} 个)")
                for c in candidates:
                    print(f"    {c['ticker']:>12s}  {c['name']:<16s}  [{c['market']}]  {c['raw_source']}")

    # 输出潜在候选关键词清单
    if keyword_candidates:
        print("\n" + "-" * 60)
        print("潜在候选关键词清单（待外部数据补全代码）：")
        print("-" * 60)
        for us_symbol, config in US_BENCHMARK_MAPPING.items():
            kc = keyword_candidates.get(us_symbol)
            if kc and kc["missing_keywords"]:
                print(f"\n  【{us_symbol} - {kc['us_name']}】({kc['mapping_type']})")
                print(f"    缺失的 A股映射: {', '.join(kc['missing_keywords'])}")

    # 结果摘要
    summary = {
        "us_benchmarks_scanned": len(US_BENCHMARK_MAPPING),
        "existing_count": len(existing_codes),
        "db_stock_count": len(all_stocks),
        "new_candidates": len(matched),
        "keyword_candidates": total_kw,
        "dry_run": dry_run,
        "discovery_date": discovery_date,
    }

    print(f"\n{'=' * 60}")
    print("扫描完成！")
    print(f"  美股对标数: {summary['us_benchmarks_scanned']}")
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
    parser = argparse.ArgumentParser(description="美股对标映射扩展扫描管道")
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
        print("[early-exit] 美股对标扩展扫描未执行。")
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
