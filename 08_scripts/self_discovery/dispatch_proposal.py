#!/usr/bin/env python3
"""
人工批准/拒绝 discovery_proposal 脚本（dispatch_proposal）

功能：
    1. 列出 discovery_proposal 表中待批准（pending_approval）的提案
    2. 批准单个/全部提案 —— 批准后写入 stock_pool 表（pool_type='candidate'），并更新提案状态为 'approved'
    3. 拒绝单个/全部提案 —— 更新提案状态为 'rejected'，不写入 stock_pool
    4. 尊重硬约束 require_human_approval_before_pool = true：
       这是"人工确认入池"的唯一入口，禁止跳过本脚本直接写 stock_pool

小白讲解：
    这个脚本像"选秀节目的总导演签字笔"——
    aggregate_discovery_candidates.py 把通过 3 道门的候选写成"提案"（pending_approval），
    但提案不会自动入池。必须由人工在这个脚本上"签字批准"（approve），
    批准的标的才会被写入 stock_pool 表（正式入池）。
    如果人工觉得某个提案不行，可以"拒绝"（reject），拒绝的提案不会入池。

安全约束：
    - require_human_approval_before_pool = true 是硬约束：
      所有 discovery_proposal → stock_pool 的流转必须经过本脚本的人工确认
    - 本脚本不受 self_discovery_enabled / auto_proposal_enabled 开关控制：
      因为这是"人工操作"，不是自动流程
    - 批准动作会同时写 stock_pool（入池）+ 更新 proposal 状态（留痕）

用法：
    # 列出所有待批准提案（默认行为）
    python 08_scripts/self_discovery/dispatch_proposal.py

    # 批准单个标的
    python 08_scripts/self_discovery/dispatch_proposal.py --approve 300308.SZ

    # 拒绝单个标的
    python 08_scripts/self_discovery/dispatch_proposal.py --reject 300308.SZ --reason "估值过高"

    # 批准所有待批准提案
    python 08_scripts/self_discovery/dispatch_proposal.py --approve-all

    # 拒绝所有待批准提案
    python 08_scripts/self_discovery/dispatch_proposal.py --reject-all --reason "本轮全部放弃"

    # 指定批准人标识（默认 'human_operator'）
    python 08_scripts/self_discovery/dispatch_proposal.py --approve 300308.SZ --approved-by "lisha"

    # 只看不写（dry-run，预览批准后会做什么）
    python 08_scripts/self_discovery/dispatch_proposal.py --approve-all --dry-run
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

# 把 lib 目录加到 sys.path，方便 import smr_paths 等
sys.path.insert(0, str(PROJECT_ROOT / "08_scripts" / "lib"))


# ============================================================
# 常量定义
# ============================================================

# 提案状态常量
STATUS_PENDING = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

# 批准入池时写入 stock_pool 的 pool_type
# 小白讲解：'candidate' 表示"候选池"——通过自主发现+人工批准进入的标的，
# 区别于 'seed'（种子层，人工录入）和 'recommended'（推荐池，评分更高）
APPROVED_POOL_TYPE = "candidate"

# 默认批准人标识
DEFAULT_APPROVED_BY = "human_operator"


# ============================================================
# 工具函数
# ============================================================

def get_db_conn() -> sqlite3.Connection:
    """
    获取数据库连接，并设置 row_factory 为 Row（支持按列名访问）。

    小白讲解：打开数据库，并设置成"按列名读取"模式，
    这样查询结果可以用 row["ticker"] 这种方式访问，比 row[0] 更清晰。

    返回：
        sqlite3.Connection：数据库连接

    异常：
        FileNotFoundError: 数据库文件不存在时抛出
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库文件不存在：{DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_policy() -> dict:
    """
    从 opportunity_engine_policy.json 读取 self_discovery_policy 配置。

    小白讲解：读配置文件，主要看 require_human_approval_before_pool 是不是 true。
    这个硬约束确保"所有提案必须人工确认才能入池"。

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
        return defaults

    try:
        content = POLICY_PATH.read_text(encoding="utf-8")
        full_config = json.loads(content)
        policy = full_config.get("self_discovery_policy", {})
        result = defaults.copy()
        result.update(policy)
        return result
    except (json.JSONDecodeError, KeyError):
        return defaults


def ensure_proposal_table(conn):
    """
    确保 discovery_proposal 表存在（防止首次运行时表缺失）。

    小白讲解：如果数据库里还没有 discovery_proposal 表，就先建出来。
    这样首次运行脚本时不会报错。

    参数：
        conn: 数据库连接
    """
    conn.execute("""
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
    """)
    conn.commit()


def relation_exists(conn, name: str) -> bool:
    """
    检查表或视图是否存在。

    小白讲解：查一下数据库里有没有这个名字的表或视图。

    参数：
        conn: 数据库连接
        name: 表名或视图名

    返回：
        bool：存在返回 True，不存在返回 False
    """
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


# ============================================================
# 列出提案
# ============================================================

def list_proposals(conn, status: str = STATUS_PENDING) -> list:
    """
    从 discovery_proposal 表读取指定状态的提案。

    小白讲解：从"提案表"里把待批准的提案捞出来，显示给人工看。
    默认只看 pending_approval（待批准）的，也可以传 'approved' 或 'rejected'
    查看历史记录。

    参数：
        conn: 数据库连接
        status: 提案状态，默认 'pending_approval'

    返回：
        list：提案列表，每条是一个 dict，包含
              proposal_id, ticker, name, market, sector, composite_score,
              score_card_json, discovery_evidence_json, reason, created_at
    """
    rows = conn.execute(
        """
        SELECT proposal_id, ticker, name, market, sector,
               composite_score, score_card_json, discovery_evidence_json,
               status, approved_by, approved_at, reason, created_at
        FROM discovery_proposal
        WHERE status = ?
        ORDER BY
            CASE WHEN composite_score IS NULL THEN 1 ELSE 0 END,
            composite_score DESC,
            created_at ASC
        """,
        (status,),
    ).fetchall()

    return [dict(row) for row in rows]


def render_proposals_table(proposals: list, status_label: str = "待批准") -> None:
    """
    以表格形式打印提案列表到控制台。

    小白讲解：把提案列成一个漂亮的表格打印出来，让人工能一眼看清
    每个提案的代码、名称、评分、发现方法等信息。

    参数：
        proposals: list_proposals 返回的提案列表
        status_label: 状态标签（如"待批准"/"已批准"/"已拒绝"），用于显示
    """
    print(f"\n{'=' * 80}")
    print(f"{status_label}的 discovery_proposal 提案（共 {len(proposals)} 条）")
    print(f"{'=' * 80}")

    if not proposals:
        print(f"  （没有 {status_label} 的提案）")
        return

    # 表头
    print(f"{'ID':>4s}  {'代码':<14s}  {'名称':<16s}  {'市场':<4s}  {'主题':<24s}  {'评分':>6s}  {'创建时间':<20s}")
    print(f"{'-' * 4}  {'-' * 14}  {'-' * 16}  {'-' * 4}  {'-' * 24}  {'-' * 6}  {'-' * 20}")

    for p in proposals:
        score = p.get("composite_score")
        score_str = f"{score:.2f}" if score is not None else "N/A"
        sector = (p.get("sector") or "")[:24]
        name = (p.get("name") or p.get("ticker") or "")[:16]
        market = (p.get("market") or "")[:4]
        created = (p.get("created_at") or "")[:20]
        print(f"{p['proposal_id']:>4d}  {p['ticker']:<14s}  {name:<16s}  {market:<4s}  {sector:<24s}  {score_str:>6s}  {created:<20s}")

    # 显示每条提案的详细证据
    print(f"\n--- 提案详情 ---")
    for p in proposals:
        print(f"\n  [{p['proposal_id']}] {p['ticker']}  {p.get('name') or ''}")
        if p.get("reason"):
            print(f"      推荐理由: {p['reason']}")
        if p.get("score_card_json"):
            try:
                score_card = json.loads(p["score_card_json"])
                dims = []
                for key in ("fundamental_quality", "valuation_position",
                            "technical_momentum", "theme_relevance", "industry_position"):
                    val = score_card.get(key)
                    if val is not None:
                        dims.append(f"{key}={val:.1f}")
                if dims:
                    print(f"      VFM 5维: {', '.join(dims)}")
                red_flags = score_card.get("red_flags", [])
                if red_flags:
                    print(f"      红旗警示: {red_flags}")
            except json.JSONDecodeError:
                print(f"      [评分卡JSON解析失败]")
        if p.get("discovery_evidence_json"):
            try:
                evidence = json.loads(p["discovery_evidence_json"])
                methods = evidence.get("methods", [])
                hit = evidence.get("hit_methods", 0)
                if methods:
                    print(f"      发现方法: {', '.join(methods)}（共 {hit} 次命中）")
            except json.JSONDecodeError:
                pass


# ============================================================
# 批准提案（写入 stock_pool）
# ============================================================

def write_to_stock_pool(conn, proposal: dict, approved_by: str, event_time: str) -> bool:
    """
    将已批准的提案写入 stock_pool 表（正式入池）。

    小白讲解：这是"入池"动作——把批准的标的写进 stock_pool 表，
    pool_type 设为 'candidate'（候选池），status 设为 'active'。
    写入后，机会雷达等其他脚本就能从 stock_pool 看到这个新标的了。

    参数：
        conn: 数据库连接
        proposal: 提案 dict（来自 list_proposals）
        approved_by: 批准人标识
        event_time: 批准时间字符串

    返回：
        bool：写入成功返回 True
    """
    ticker = proposal["ticker"]
    sector = proposal.get("sector")
    score = proposal.get("composite_score")
    proposal_id = proposal["proposal_id"]

    # 写入理由：包含提案 ID 和批准人，方便追溯
    added_reason = (
        f"approved from discovery_proposal (proposal_id={proposal_id}, "
        f"approved_by={approved_by})"
    )

    conn.execute(
        """
        INSERT OR REPLACE INTO stock_pool
            (pool_type, ts_code, sector, added_date, added_reason, score, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        """,
        (APPROVED_POOL_TYPE, ticker, sector, event_time, added_reason, score),
    )
    return True


def approve_proposal(conn, ticker: str, approved_by: str = DEFAULT_APPROVED_BY,
                     reason: str = "", dry_run: bool = False) -> dict:
    """
    批准单个提案：写入 stock_pool + 更新 proposal 状态为 'approved'。

    小白讲解：这是"签字批准"动作——
    1. 先从 discovery_proposal 表找到这个 ticker 的 pending 提案
    2. 把它写入 stock_pool 表（pool_type='candidate', status='active'）
    3. 更新 proposal 的 status='approved'，记下批准人和时间

    参数：
        conn: 数据库连接
        ticker: 要批准的股票代码
        approved_by: 批准人标识，默认 'human_operator'
        reason: 批准理由（可选）
        dry_run: 如果 True，只预览不写入

    返回：
        dict：操作结果 {
            "ticker": str,
            "action": "approved" / "not_found" / "already_processed",
            "dry_run": bool,
            "proposal_id": int or None,
            "message": str,
        }
    """
    # 查找 pending 提案
    row = conn.execute(
        "SELECT * FROM discovery_proposal WHERE ticker=? AND status=?",
        (ticker, STATUS_PENDING),
    ).fetchone()

    if row is None:
        # 检查是否已经处理过
        existing = conn.execute(
            "SELECT status FROM discovery_proposal WHERE ticker=?",
            (ticker,),
        ).fetchone()
        if existing is not None:
            return {
                "ticker": ticker,
                "action": "already_processed",
                "dry_run": dry_run,
                "proposal_id": None,
                "message": f"提案 {ticker} 已处理过（状态: {existing['status']}），不能重复批准",
            }
        return {
            "ticker": ticker,
            "action": "not_found",
            "dry_run": dry_run,
            "proposal_id": None,
            "message": f"未找到 {ticker} 的 pending_approval 提案",
        }

    proposal = dict(row)
    event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if dry_run:
        return {
            "ticker": ticker,
            "action": "approved",
            "dry_run": True,
            "proposal_id": proposal["proposal_id"],
            "message": (
                f"[dry-run] 将批准 {ticker}：写入 stock_pool(pool_type={APPROVED_POOL_TYPE}), "
                f"更新 proposal 状态为 approved"
            ),
        }

    # 正式执行：写 stock_pool + 更新 proposal
    write_to_stock_pool(conn, proposal, approved_by, event_time)
    conn.execute(
        """
        UPDATE discovery_proposal
        SET status=?, approved_by=?, approved_at=?, reason=?
        WHERE ticker=? AND status=?
        """,
        (STATUS_APPROVED, approved_by, event_time, reason or "人工批准入池",
         ticker, STATUS_PENDING),
    )
    conn.commit()

    return {
        "ticker": ticker,
        "action": "approved",
        "dry_run": False,
        "proposal_id": proposal["proposal_id"],
        "message": (
            f"已批准 {ticker}：写入 stock_pool(pool_type={APPROVED_POOL_TYPE}, status=active), "
            f"proposal 状态更新为 approved"
        ),
    }


def reject_proposal(conn, ticker: str, approved_by: str = DEFAULT_APPROVED_BY,
                    reason: str = "", dry_run: bool = False) -> dict:
    """
    拒绝单个提案：只更新 proposal 状态为 'rejected'，不写入 stock_pool。

    小白讲解：这是"拒绝"动作——
    只更新 proposal 的 status='rejected'，记下拒绝人和理由，
    不会写入 stock_pool（不入池）。

    参数：
        conn: 数据库连接
        ticker: 要拒绝的股票代码
        approved_by: 拒绝人标识
        reason: 拒绝理由（建议填写）
        dry_run: 如果 True，只预览不写入

    返回：
        dict：操作结果，结构同 approve_proposal
    """
    row = conn.execute(
        "SELECT * FROM discovery_proposal WHERE ticker=? AND status=?",
        (ticker, STATUS_PENDING),
    ).fetchone()

    if row is None:
        existing = conn.execute(
            "SELECT status FROM discovery_proposal WHERE ticker=?",
            (ticker,),
        ).fetchone()
        if existing is not None:
            return {
                "ticker": ticker,
                "action": "already_processed",
                "dry_run": dry_run,
                "proposal_id": None,
                "message": f"提案 {ticker} 已处理过（状态: {existing['status']}），不能重复拒绝",
            }
        return {
            "ticker": ticker,
            "action": "not_found",
            "dry_run": dry_run,
            "proposal_id": None,
            "message": f"未找到 {ticker} 的 pending_approval 提案",
        }

    proposal = dict(row)
    event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if dry_run:
        return {
            "ticker": ticker,
            "action": "rejected",
            "dry_run": True,
            "proposal_id": proposal["proposal_id"],
            "message": f"[dry-run] 将拒绝 {ticker}：更新 proposal 状态为 rejected（不写 stock_pool）",
        }

    conn.execute(
        """
        UPDATE discovery_proposal
        SET status=?, approved_by=?, approved_at=?, reason=?
        WHERE ticker=? AND status=?
        """,
        (STATUS_REJECTED, approved_by, event_time,
         reason or "人工拒绝，不入池", ticker, STATUS_PENDING),
    )
    conn.commit()

    return {
        "ticker": ticker,
        "action": "rejected",
        "dry_run": False,
        "proposal_id": proposal["proposal_id"],
        "message": f"已拒绝 {ticker}：proposal 状态更新为 rejected（未写 stock_pool）",
    }


def approve_all(conn, approved_by: str = DEFAULT_APPROVED_BY,
                reason: str = "", dry_run: bool = False) -> list:
    """
    批准所有 pending_approval 提案。

    小白讲解：一次性批准所有待批准的提案，相当于"全部签字"。
    每个提案都会写 stock_pool + 更新状态为 approved。

    参数：
        conn: 数据库连接
        approved_by: 批准人标识
        reason: 批准理由
        dry_run: 如果 True，只预览不写入

    返回：
        list：每个提案的操作结果（dict 列表）
    """
    pending = list_proposals(conn, STATUS_PENDING)
    results = []
    for proposal in pending:
        result = approve_proposal(
            conn, proposal["ticker"], approved_by, reason, dry_run
        )
        results.append(result)
    return results


def reject_all(conn, approved_by: str = DEFAULT_APPROVED_BY,
               reason: str = "", dry_run: bool = False) -> list:
    """
    拒绝所有 pending_approval 提案。

    小白讲解：一次性拒绝所有待批准的提案，相当于"全部否决"。
    只更新状态为 rejected，不写 stock_pool。

    参数：
        conn: 数据库连接
        approved_by: 拒绝人标识
        reason: 拒绝理由
        dry_run: 如果 True，只预览不写入

    返回：
        list：每个提案的操作结果（dict 列表）
    """
    pending = list_proposals(conn, STATUS_PENDING)
    results = []
    for proposal in pending:
        result = reject_proposal(
            conn, proposal["ticker"], approved_by, reason, dry_run
        )
        results.append(result)
    return results


# ============================================================
# 主流程
# ============================================================

def run_dispatch(args) -> int:
    """
    人工批准/拒绝主流程。

    小白讲解：根据命令行参数执行对应操作——
    - 没有参数：列出所有待批准提案
    - --approve TICKER：批准单个
    - --reject TICKER：拒绝单个
    - --approve-all：批准所有
    - --reject-all：拒绝所有

    参数：
        args: argparse 解析后的参数对象

    返回：
        int：退出码（0 成功，1 失败）
    """
    print("=" * 80)
    print("人工批准/拒绝 discovery_proposal 脚本（dispatch_proposal）")
    print("=" * 80)

    # 检查硬约束
    policy = load_policy()
    require_human = policy.get("require_human_approval_before_pool", True)
    print(f"\n[配置] require_human_approval_before_pool = {require_human}")
    print(f"[配置] 批准入池 pool_type = {APPROVED_POOL_TYPE}")
    print(f"[配置] 批准人 = {args.approved_by}")
    if args.dry_run:
        print(f"[配置] dry-run 模式：只预览不写入")

    if not require_human:
        print(f"[警告] require_human_approval_before_pool=False，但仍建议通过本脚本批准以留痕")

    # 连接数据库
    try:
        conn = get_db_conn()
    except FileNotFoundError as e:
        print(f"\n[错误] {e}")
        return 1

    ensure_proposal_table(conn)

    # 检查 stock_pool 表是否存在（批准操作需要）
    stock_pool_exists = relation_exists(conn, "stock_pool")
    if not stock_pool_exists and not args.dry_run:
        print(f"\n[警告] stock_pool 表不存在，批准操作将失败（拒绝操作不受影响）")

    exit_code = 0

    try:
        # 默认行为：列出待批准提案
        if not any([args.approve, args.reject, args.approve_all, args.reject_all]):
            pending = list_proposals(conn, STATUS_PENDING)
            render_proposals_table(pending, "待批准")

            # 如果有已批准/已拒绝的历史，也显示计数
            approved = list_proposals(conn, STATUS_APPROVED)
            rejected = list_proposals(conn, STATUS_REJECTED)
            print(f"\n--- 历史统计 ---")
            print(f"  待批准: {len(pending)} 条")
            print(f"  已批准: {len(approved)} 条")
            print(f"  已拒绝: {len(rejected)} 条")

            if pending:
                print(f"\n--- 操作提示 ---")
                print(f"  批准单个: python {Path(__file__).name} --approve <ticker>")
                print(f"  拒绝单个: python {Path(__file__).name} --reject <ticker> --reason '理由'")
                print(f"  批准所有: python {Path(__file__).name} --approve-all")
                print(f"  拒绝所有: python {Path(__file__).name} --reject-all --reason '理由'")
                print(f"  预览不写: 加 --dry-run 参数")
            return 0

        # 批准单个
        if args.approve:
            result = approve_proposal(
                conn, args.approve, args.approved_by, args.reason or "", args.dry_run
            )
            print(f"\n[结果] {result['message']}")
            if result["action"] == "not_found":
                exit_code = 1

        # 拒绝单个
        if args.reject:
            result = reject_proposal(
                conn, args.reject, args.approved_by, args.reason or "", args.dry_run
            )
            print(f"\n[结果] {result['message']}")
            if result["action"] == "not_found":
                exit_code = 1

        # 批准所有
        if args.approve_all:
            results = approve_all(
                conn, args.approved_by, args.reason or "", args.dry_run
            )
            print(f"\n[结果] 批准所有提案：共 {len(results)} 条")
            success = sum(1 for r in results if r["action"] == "approved")
            print(f"  成功: {success} 条")
            for r in results:
                print(f"  - {r['message']}")

        # 拒绝所有
        if args.reject_all:
            results = reject_all(
                conn, args.approved_by, args.reason or "", args.dry_run
            )
            print(f"\n[结果] 拒绝所有提案：共 {len(results)} 条")
            success = sum(1 for r in results if r["action"] == "rejected")
            print(f"  成功: {success} 条")
            for r in results:
                print(f"  - {r['message']}")

        # 操作后显示剩余待批准提案
        if any([args.approve, args.reject, args.approve_all, args.reject_all]):
            remaining = list_proposals(conn, STATUS_PENDING)
            print(f"\n--- 操作后剩余待批准提案：{len(remaining)} 条 ---")
            if remaining:
                render_proposals_table(remaining, "待批准")

    finally:
        conn.close()

    return exit_code


# ============================================================
# 命令行入口
# ============================================================

def main():
    """
    命令行入口函数。

    支持参数：
        --approve TICKER: 批准单个标的
        --reject TICKER: 拒绝单个标的
        --approve-all: 批准所有待批准提案
        --reject-all: 拒绝所有待批准提案
        --approved-by NAME: 批准人标识（默认 'human_operator'）
        --reason TEXT: 批准/拒绝理由
        --dry-run: 只预览不写入
    """
    parser = argparse.ArgumentParser(
        description="人工批准/拒绝 discovery_proposal 提案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 列出所有待批准提案
  python dispatch_proposal.py

  # 批准单个标的
  python dispatch_proposal.py --approve 300308.SZ

  # 拒绝单个标的并填写理由
  python dispatch_proposal.py --reject 300308.SZ --reason "估值过高"

  # 批准所有待批准提案
  python dispatch_proposal.py --approve-all

  # 预览批准所有（不写入）
  python dispatch_proposal.py --approve-all --dry-run
        """,
    )
    parser.add_argument(
        "--approve", metavar="TICKER",
        help="批准单个标的（指定 ticker，如 300308.SZ）",
    )
    parser.add_argument(
        "--reject", metavar="TICKER",
        help="拒绝单个标的（指定 ticker）",
    )
    parser.add_argument(
        "--approve-all", action="store_true",
        help="批准所有待批准提案",
    )
    parser.add_argument(
        "--reject-all", action="store_true",
        help="拒绝所有待批准提案",
    )
    parser.add_argument(
        "--approved-by", default=DEFAULT_APPROVED_BY,
        help=f"批准人标识（默认 '{DEFAULT_APPROVED_BY}'）",
    )
    parser.add_argument(
        "--reason", default="",
        help="批准/拒绝理由（建议填写）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只预览不写入数据库",
    )

    args = parser.parse_args()

    # 互斥检查
    actions = [args.approve, args.reject, args.approve_all, args.reject_all]
    active_actions = sum(1 for a in actions if a)
    if active_actions > 1:
        print("[错误] --approve / --reject / --approve-all / --reject-all 不能同时使用")
        return 1

    return run_dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
