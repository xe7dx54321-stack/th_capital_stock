#!/usr/bin/env python3
"""
候选聚合与去重管道（aggregate_discovery_candidates pipeline）

功能：
    1. 从 discovery_candidate 表读取所有候选（来自 theme_extension / supply_chain / us_benchmark）
    2. 按 ticker 去重，统计每个 ticker 被多少个发现方法命中（hit_methods，置信度信号）
    3. 对候选做 VFM 评分（通过 API 调用，如果可用）
    4. 通过 3 道门筛选：
       - 门 1：composite_score >= 4.0，无 red_flag 中的严重项
       - 门 2：theme_relevance >= 5.0 或 industry_position >= 6.0
       - 门 3：technical_momentum >= 5.0 或反转/突破信号
    5. 通过 3 道门的候选提案到 discovery_proposal 表（受门禁开关控制）

小白讲解：
    这个脚本像"选秀节目的总导演"——把三个"星探"（主题扩展、供应链扩展、美股对标扩展）
    发现的候选汇总到一起，去掉重复的，统计每个候选被几个星探同时看中（被多个星探
    看中的更可信）。然后给候选打分（VFM 评分），通过三道考试（3 道门）的才能
    "晋级提案"，等待人工确认后才能正式入池。

安全约束：
    - self_discovery_enabled = False 时：可以手动运行验证管线，但不会自动提案
    - auto_proposal_enabled = False 时：只输出筛选结果，不写入 discovery_proposal
    - require_human_approval_before_pool = true（硬约束）：永远不会自动写入 stock_pool

用法：
    python 08_scripts/self_discovery/aggregate_discovery_candidates.py
    python 08_scripts/self_discovery/aggregate_discovery_candidates.py --dry-run   # 只看不写
    python 08_scripts/self_discovery/aggregate_discovery_candidates.py --force-proposal  # 强制提案（忽略 auto_proposal_enabled）
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径处理
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "01_data" / "db" / "smr.db"
POLICY_PATH = PROJECT_ROOT / "00_control" / "opportunity_engine_policy.json"

# 把 lib 目录加到 sys.path，方便 import smr_guard
sys.path.insert(0, str(PROJECT_ROOT / "08_scripts" / "lib"))

try:
    from smr_guard import Guard  # noqa: E402
except ImportError:
    # 如果 import 失败，用降级方式（不检查门禁开关）
    Guard = None


# ============================================================
# 3 道门阈值定义
# ============================================================

# 小白讲解：这 3 道门就像选秀节目的三轮考试，
# 候选必须全部通过才能晋级提案。
GATE_THRESHOLDS = {
    "gate1": {
        "name": "基本过滤",
        "description": "composite_score >= 4.0，无 red_flag 中的严重项",
        "min_composite": 4.0,
        "severe_red_flags": ["ST", "连续亏损", "退市风险", "极高估值"],
    },
    "gate2": {
        "name": "主题相关性",
        "description": "theme_relevance >= 5.0 或 industry_position >= 6.0",
        "min_theme_relevance": 5.0,
        "min_industry_position": 6.0,
    },
    "gate3": {
        "name": "技术面有吸引力",
        "description": "technical_momentum >= 5.0 或反转/突破信号",
        "min_technical_momentum": 5.0,
    },
}


# ============================================================
# 读取策略配置
# ============================================================

def load_policy() -> dict:
    """
    从 opportunity_engine_policy.json 读取 self_discovery_policy 配置。

    小白讲解：读配置文件，看自主发现管线的"规则"是什么——
    比如每个主题最多发现几个候选、提案的最低评分是多少等。

    返回：
        dict：self_discovery_policy 配置，读不到就用默认值
    """
    defaults = {
        "mode": "development",
        "max_candidates_per_theme": 8,
        "min_composite_score_for_proposal": 6.0,
        "require_human_approval_before_pool": True,
        "scan_schedule": "weekly",
    }

    if not POLICY_PATH.exists():
        print(f"[警告] 策略文件不存在：{POLICY_PATH}，使用默认配置")
        return defaults

    try:
        content = POLICY_PATH.read_text(encoding="utf-8")
        full_config = json.loads(content)
        policy = full_config.get("self_discovery_policy", {})
        # 合并默认值
        result = defaults.copy()
        result.update(policy)
        return result
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[警告] 策略文件解析失败：{e}，使用默认配置")
        return defaults


def check_guard_switches() -> dict:
    """
    检查 smr_guard 的安全开关状态。

    小白讲解：检查"门禁开关"是不是开着——
    - self_discovery_enabled：自主发现管线是否启用
    - auto_proposal_enabled：是否允许自动提案

    返回：
        dict：{"self_discovery_enabled": bool, "auto_proposal_enabled": bool}
    """
    if Guard is None:
        # import 失败，返回安全默认值
        return {"self_discovery_enabled": False, "auto_proposal_enabled": False}

    boundary = Guard.SAFETY_BOUNDARY
    return {
        "self_discovery_enabled": boundary.get("self_discovery_enabled", False),
        "auto_proposal_enabled": boundary.get("auto_proposal_enabled", False),
    }


# ============================================================
# 候选聚合与去重
# ============================================================

def load_and_aggregate_candidates(conn) -> list:
    """
    从 discovery_candidate 表读取所有候选，按 ticker 聚合去重。

    小白讲解：把三个"星探"找到的候选汇总，如果同一只股票被多个星探
    同时发现，就合并成一条记录，并记下"被几个方法命中"。

    参数：
        conn: 数据库连接

    返回：
        list：去重后的候选列表，每条包含
              ticker, name, market, sector, hit_methods, methods, discovery_date, sources
    """
    # 检查表是否存在
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='discovery_candidate'"
    )
    if cursor.fetchone() is None:
        return []

    rows = conn.execute("""
        SELECT ticker, name, market, sector, discovery_method,
               hit_methods, discovery_date, raw_source
        FROM discovery_candidate
        ORDER BY ticker, discovery_method
    """).fetchall()

    # 按 ticker 聚合
    aggregated = {}
    for row in rows:
        ticker = row["ticker"]
        if ticker not in aggregated:
            aggregated[ticker] = {
                "ticker": ticker,
                "name": row["name"] or ticker,
                "market": row["market"] or "",
                "sector": row["sector"] or "",
                "hit_methods": 0,
                "methods": [],
                "discovery_date": row["discovery_date"],
                "sources": [],
            }
        entry = aggregated[ticker]
        entry["hit_methods"] += 1
        if row["discovery_method"] not in entry["methods"]:
            entry["methods"].append(row["discovery_method"])
        if row["raw_source"]:
            entry["sources"].append(row["raw_source"])

    return list(aggregated.values())


# ============================================================
# VFM 评分获取（通过 API）
# ============================================================

def fetch_vfm_scores(tickers: list, api_url: str = "http://127.0.0.1:3000/api/value-scores") -> dict:
    """
    通过 API 获取候选标的的 VFM 评分。

    小白讲解：给候选股票打分（VFM 5 维评分），需要调用后端 API。
    如果 API 不可用或没有数据，返回空字典，后续降级为"待评分"模式。

    参数：
        tickers: 股票代码列表
        api_url: API 地址

    返回：
        dict：{ticker: vfm_score_card}，如果 API 不可用返回空字典
    """
    if not tickers:
        return {}

    try:
        import urllib.request
        import urllib.error

        with urllib.request.urlopen(api_url, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))

        # API 返回格式：[{tsCode, vfmScoreCard: {...}}, ...]
        scores = {}
        for item in data:
            ts_code = item.get("tsCode") or item.get("ts_code")
            vfm = item.get("vfmScoreCard") or item.get("vfm_score_card")
            if ts_code and vfm:
                scores[ts_code] = vfm

        return scores
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            ConnectionError, TimeoutError, OSError):
        # API 不可用，返回空字典
        return {}
    except Exception:
        # 其他异常也返回空字典（降级处理）
        return {}


# ============================================================
# 3 道门筛选
# ============================================================

def check_gate1(candidate: dict, vfm_score: dict) -> tuple:
    """
    门 1：基本过滤（composite_score >= 4.0，无 red_flag 中的严重项）。

    小白讲解：第一道考试——看候选的"综合分数"够不够 4 分，
    而且不能有严重的"红旗"警示（如 ST、连续亏损等）。

    参数：
        candidate: 候选标的信息
        vfm_score: VFM 评分卡（可能为空字典）

    返回：
        (passed: bool, reason: str)
    """
    if not vfm_score:
        # 没有 VFM 数据，降级处理：只看 hit_methods
        if candidate.get("hit_methods", 0) >= 2:
            return True, "无VFM数据，但被多个方法命中（>=2），通过门1"
        return False, "无VFM数据且命中方法<2，待评分"

    composite = vfm_score.get("composite_score", 0)
    red_flags = vfm_score.get("red_flags", [])
    severe_flags = GATE_THRESHOLDS["gate1"]["severe_red_flags"]

    # 检查 composite_score
    if composite < GATE_THRESHOLDS["gate1"]["min_composite"]:
        return False, f"composite_score={composite} < 4.0"

    # 检查严重 red_flag
    for flag in red_flags:
        for severe in severe_flags:
            if severe in str(flag):
                return False, f"严重red_flag: {flag}"

    return True, f"composite_score={composite}，无严重red_flag"


def check_gate2(candidate: dict, vfm_score: dict) -> tuple:
    """
    门 2：主题相关性（theme_relevance >= 5.0 或 industry_position >= 6.0）。

    小白讲解：第二道考试——看候选和我们关注的 5 大主题相关性够不够。
    主题相关性 >= 5 分，或者产业位置 >= 6 分，就能通过。

    参数：
        candidate: 候选标的信息
        vfm_score: VFM 评分卡

    返回：
        (passed: bool, reason: str)
    """
    if not vfm_score:
        # 没有 VFM 数据，但如果候选有 sector 标签，说明和主题相关
        if candidate.get("sector"):
            return True, "无VFM数据，但已匹配到主题sector，通过门2"
        return False, "无VFM数据且无sector标签，待评分"

    theme_rel = vfm_score.get("theme_relevance", 0)
    ind_pos = vfm_score.get("industry_position", 0)

    if theme_rel >= GATE_THRESHOLDS["gate2"]["min_theme_relevance"]:
        return True, f"theme_relevance={theme_rel} >= 5.0"

    if ind_pos >= GATE_THRESHOLDS["gate2"]["min_industry_position"]:
        return True, f"industry_position={ind_pos} >= 6.0"

    return False, f"theme_relevance={theme_rel}<5.0 且 industry_position={ind_pos}<6.0"


def check_gate3(candidate: dict, vfm_score: dict) -> tuple:
    """
    门 3：技术面有吸引力（technical_momentum >= 5.0 或反转/突破信号）。

    小白讲解：第三道考试——看候选的技术面好不好。
    技术动量 >= 5 分，或者有"反转/突破"信号，就能通过。

    参数：
        candidate: 候选标的信息
        vfm_score: VFM 评分卡

    返回：
        (passed: bool, reason: str)
    """
    if not vfm_score:
        # 没有 VFM 数据，降级处理
        return False, "无VFM数据，technical_momentum无法评估，待评分"

    tech_mom = vfm_score.get("technical_momentum", 0)

    if tech_mom >= GATE_THRESHOLDS["gate3"]["min_technical_momentum"]:
        return True, f"technical_momentum={tech_mom} >= 5.0"

    # 检查反转/突破信号（red_flags 里可能有，或 score_detail 里有信号）
    red_flags = vfm_score.get("red_flags", [])
    for flag in red_flags:
        flag_str = str(flag)
        if "反转" in flag_str or "突破" in flag_str:
            return True, f"检测到信号: {flag}"

    return False, f"technical_momentum={tech_mom}<5.0 且无反转/突破信号"


def run_three_gates(candidate: dict, vfm_score: dict) -> dict:
    """
    运行 3 道门筛选。

    小白讲解：让候选依次通过三道考试，记录每道考试的结果。

    参数：
        candidate: 候选标的信息
        vfm_score: VFM 评分卡

    返回：
        dict：{
            "passed": bool,           # 是否全部通过
            "gate1": (passed, reason),
            "gate2": (passed, reason),
            "gate3": (passed, reason),
        }
    """
    g1 = check_gate1(candidate, vfm_score)
    g2 = check_gate2(candidate, vfm_score)
    g3 = check_gate3(candidate, vfm_score)

    all_passed = g1[0] and g2[0] and g3[0]

    return {
        "passed": all_passed,
        "gate1": g1,
        "gate2": g2,
        "gate3": g3,
    }


# ============================================================
# 提案到 discovery_proposal 表
# ============================================================

def write_proposal(conn, candidate: dict, vfm_score: dict, gate_result: dict) -> bool:
    """
    将通过 3 道门的候选提案到 discovery_proposal 表。

    小白讲解：通过的候选写进"提案表"（discovery_proposal），
    等待人工确认。提案状态默认是 'pending_approval'（待批准）。

    参数：
        conn: 数据库连接
        candidate: 候选标的信息
        vfm_score: VFM 评分卡
        gate_result: 3 道门结果

    返回：
        bool：是否成功写入
    """
    try:
        # 构建推荐理由
        reasons = []
        reasons.append(f"命中 {candidate['hit_methods']} 个发现方法: {', '.join(candidate['methods'])}")
        if vfm_score:
            composite = vfm_score.get("composite_score", 0)
            reasons.append(f"VFM综合评分: {composite}")
        reasons.append(f"门1: {gate_result['gate1'][1]}")
        reasons.append(f"门2: {gate_result['gate2'][1]}")
        reasons.append(f"门3: {gate_result['gate3'][1]}")
        reason_text = " | ".join(reasons)

        # 构建发现证据
        evidence = {
            "methods": candidate["methods"],
            "sources": candidate["sources"],
            "hit_methods": candidate["hit_methods"],
            "gate_results": {
                "gate1": {"passed": gate_result["gate1"][0], "reason": gate_result["gate1"][1]},
                "gate2": {"passed": gate_result["gate2"][0], "reason": gate_result["gate2"][1]},
                "gate3": {"passed": gate_result["gate3"][0], "reason": gate_result["gate3"][1]},
            },
        }

        composite_score = vfm_score.get("composite_score") if vfm_score else None
        score_card_json = json.dumps(vfm_score, ensure_ascii=False) if vfm_score else None

        conn.execute("""
            INSERT INTO discovery_proposal
                (ticker, name, market, sector, composite_score,
                 score_card_json, discovery_evidence_json,
                 status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?)
            ON CONFLICT(ticker) DO UPDATE SET
                composite_score = excluded.composite_score,
                score_card_json = excluded.score_card_json,
                discovery_evidence_json = excluded.discovery_evidence_json,
                reason = excluded.reason
        """, (
            candidate["ticker"], candidate["name"], candidate["market"],
            candidate["sector"], composite_score,
            score_card_json, json.dumps(evidence, ensure_ascii=False),
            reason_text
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"[错误] 写入提案失败 {candidate['ticker']}: {e}")
        return False


# ============================================================
# 确保表存在
# ============================================================

def ensure_tables(conn):
    """确保 discovery_candidate 和 discovery_proposal 表存在"""
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


# ============================================================
# 主流程
# ============================================================

def run_aggregate(dry_run: bool = False, force_proposal: bool = False) -> dict:
    """
    候选聚合与 3 道门筛选主流程。

    小白讲解：这是"选秀总导演"函数，按以下步骤执行：
    1. 检查门禁开关和策略配置
    2. 从数据库读取所有候选并聚合去重
    3. 获取 VFM 评分（通过 API）
    4. 对每个候选运行 3 道门筛选
    5. 通过的候选提案到 discovery_proposal（受门禁开关控制）
    6. 输出筛选摘要

    参数：
        dry_run: 只看不写
        force_proposal: 强制提案（忽略 auto_proposal_enabled 开关）

    返回：
        dict：聚合筛选摘要
    """
    print("=" * 60)
    print("候选聚合与去重管道（aggregate_discovery_candidates pipeline）")
    print("=" * 60)

    # 步骤 1：检查门禁开关和策略
    switches = check_guard_switches()
    policy = load_policy()
    print(f"\n[1/6] 门禁开关状态：")
    print(f"       self_discovery_enabled: {switches['self_discovery_enabled']}")
    print(f"       auto_proposal_enabled: {switches['auto_proposal_enabled']}")
    print(f"       策略模式: {policy['mode']}")
    print(f"       最低提案评分: {policy['min_composite_score_for_proposal']}")
    print(f"       需人工确认入池: {policy['require_human_approval_before_pool']}")

    if not switches["self_discovery_enabled"]:
        print(f"       [提示] 自主发现管线未启用（开发模式），可手动运行验证管线")

    # 步骤 2：读取并聚合候选
    if not DB_PATH.exists():
        print(f"\n[错误] 数据库不存在：{DB_PATH}")
        return {"error": "database_not_found"}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ensure_tables(conn)

    candidates = load_and_aggregate_candidates(conn)
    print(f"\n[2/6] 从 discovery_candidate 表读取并聚合：{len(candidates)} 个去重候选")

    if not candidates:
        print("       （表为空，请先运行 scan_theme_extension / scan_supply_chain_extension / scan_us_benchmark_extension）")
        conn.close()
        return {
            "total_candidates": 0,
            "dry_run": dry_run,
            "switches": switches,
        }

    # 显示聚合结果
    for c in candidates[:10]:  # 只显示前 10 个
        methods_str = ", ".join(c["methods"])
        print(f"       - {c['ticker']:>12s}  {c['name']:<16s}  命中{c['hit_methods']}个方法 ({methods_str})")
    if len(candidates) > 10:
        print(f"       ... 还有 {len(candidates) - 10} 个")

    # 步骤 3：获取 VFM 评分
    all_tickers = [c["ticker"] for c in candidates]
    print(f"\n[3/6] 获取 VFM 评分...")
    vfm_scores = fetch_vfm_scores(all_tickers)
    print(f"       获取到 {len(vfm_scores)} / {len(all_tickers)} 个候选的 VFM 评分")

    if not vfm_scores:
        print("       [提示] VFM API 不可用或无数据，降级为'待评分'模式")
        print("              门1/门2/门3 将使用降级规则（基于 hit_methods 和 sector）")

    # 步骤 4：3 道门筛选
    print(f"\n[4/6] 开始 3 道门筛选...")
    passed_candidates = []
    failed_candidates = []

    for c in candidates:
        vfm = vfm_scores.get(c["ticker"], {})
        gate_result = run_three_gates(c, vfm)

        if gate_result["passed"]:
            passed_candidates.append((c, vfm, gate_result))
        else:
            failed_candidates.append((c, vfm, gate_result))

    print(f"       通过 3 道门: {len(passed_candidates)} 个")
    print(f"       未通过: {len(failed_candidates)} 个")

    # 显示未通过的原因
    if failed_candidates:
        print(f"\n       未通过原因明细：")
        for c, vfm, gr in failed_candidates[:5]:
            failed_gates = []
            if not gr["gate1"][0]:
                failed_gates.append(f"门1: {gr['gate1'][1]}")
            if not gr["gate2"][0]:
                failed_gates.append(f"门2: {gr['gate2'][1]}")
            if not gr["gate3"][0]:
                failed_gates.append(f"门3: {gr['gate3'][1]}")
            print(f"       - {c['ticker']:>12s}  {', '.join(failed_gates)}")

    # 步骤 5：提案到 discovery_proposal
    print(f"\n[5/6] 提案到 discovery_proposal...")

    can_proposal = switches["auto_proposal_enabled"] or force_proposal

    if dry_run:
        print(f"       [dry-run] 不写入数据库，跳过 {len(passed_candidates)} 条提案")
    elif not can_proposal:
        print(f"       [跳过] auto_proposal_enabled=False 且未指定 --force-proposal")
        print(f"              通过的 {len(passed_candidates)} 个候选仅输出，不写入提案表")
    elif not passed_candidates:
        print(f"       没有通过 3 道门的候选，无需提案")
    else:
        written = 0
        for c, vfm, gr in passed_candidates:
            if write_proposal(conn, c, vfm, gr):
                written += 1
        print(f"       写入 discovery_proposal 表：{written} 条提案（状态: pending_approval）")
        print(f"       [提示] 所有提案需人工确认后才能写入 stock_pool（硬约束）")

    conn.close()

    # 步骤 6：输出通过的候选清单
    if passed_candidates:
        print("\n" + "-" * 60)
        print("通过 3 道门的候选清单：")
        print("-" * 60)
        for c, vfm, gr in passed_candidates:
            composite = vfm.get("composite_score", "N/A") if vfm else "N/A"
            print(f"  {c['ticker']:>12s}  {c['name']:<16s}  [{c['market']}]  "
                  f"综合评分={composite}  命中{c['hit_methods']}个方法")

    # 结果摘要
    summary = {
        "total_candidates": len(candidates),
        "vfm_scored": len(vfm_scores),
        "passed_gates": len(passed_candidates),
        "failed_gates": len(failed_candidates),
        "dry_run": dry_run,
        "auto_proposal_enabled": switches["auto_proposal_enabled"],
        "force_proposal": force_proposal,
        "require_human_approval": policy["require_human_approval_before_pool"],
    }

    print(f"\n{'=' * 60}")
    print("聚合筛选完成！")
    print(f"  候选总数（去重后）: {summary['total_candidates']}")
    print(f"  获取VFM评分: {summary['vfm_scored']}")
    print(f"  通过3道门: {summary['passed_gates']}")
    print(f"  未通过: {summary['failed_gates']}")
    print(f"  模式: {'dry-run（不写入）' if dry_run else '正式'}")
    if not dry_run:
        if can_proposal and passed_candidates:
            print(f"  提案已写入 discovery_proposal（待人工确认）")
        elif not can_proposal:
            print(f"  未提案（auto_proposal_enabled=False）")
    print(f"  人工确认入池: {'是（硬约束）' if policy['require_human_approval_before_pool'] else '否'}")
    print("=" * 60)

    return summary


# ============================================================
# 命令行入口
# ============================================================

def main():
    """
    命令行入口函数。

    支持参数：
        --dry-run: 只看不写
        --force-proposal: 强制提案（忽略 auto_proposal_enabled 开关）
    """
    parser = argparse.ArgumentParser(description="候选聚合与去重管道")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只扫描不写入数据库"
    )
    parser.add_argument(
        "--force-proposal", action="store_true",
        help="强制提案（忽略 auto_proposal_enabled 开关）"
    )
    args = parser.parse_args()

    run_aggregate(dry_run=args.dry_run, force_proposal=args.force_proposal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
