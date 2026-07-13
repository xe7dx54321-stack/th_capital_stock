#!/usr/bin/env python3
"""SMR PnL Calculator - Updates P&L for all open positions.

数据源已从旧表 position 切换为新表 paper_portfolio_positions，
解决模拟持仓数据流脱节问题（旧表 0 条记录，新表有实际 open 持仓）。
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import env_or_project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")


def fetch_latest_price(conn, ticker, market):
    """
    根据股票代码和市场类型，从对应的价格表读取最新收盘价。

    为什么要这样写：原来 pnl.py 只查 daily_bar 表（A股用的），
    但模拟持仓 paper_portfolio_positions 里有 NVDA 这种美股，
    美股价格存在 us_daily_bar 表里，代码字段叫 symbol 而不是 ts_code，
    所以要根据 market 字段选对表和字段名，否则查不到价格。

    参数：
        conn: sqlite3 数据库连接对象
        ticker: 股票代码，比如 'NVDA' 或 '000001.SZ'
        market: 市场类型，'US' 表示美股，'A' 表示A股，'H' 表示港股

    返回值：
        最新收盘价（float），如果查不到返回 None
    """
    if market == "US":
        # 美股用 us_daily_bar 表，代码字段叫 symbol
        row = conn.execute(
            "SELECT close FROM us_daily_bar WHERE symbol=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
    else:
        # A股和港股用 daily_bar 表，代码字段叫 ts_code
        row = conn.execute(
            "SELECT close FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
    return row[0] if row else None


def main():
    """
    主函数：计算所有 open 状态模拟持仓的盈亏，并注册快照、触发自动转交。

    工作流程（小白版）：
        1. 连接数据库，从 paper_portfolio_positions 表读取所有 open 持仓
        2. 对每条持仓，按市场查最新收盘价，算盈亏（pnl）和盈亏比例（pnl_pct）
        3. 把盈亏结果写回 metadata_json 的 mark_to_market 字段
           （新表没有 pnl/pnl_pct 列，按 smr_paper_portfolio.py 的约定写进 metadata_json）
        4. 调用 register_snapshot 注册 portfolio_pnl_snapshot 快照
        5. 调用 ensure_auto_handoff 触发自动转交（如果需要）
        6. 记录运行日志

    参数：无
    返回值：无
    异常：数据库连接或查询失败时会抛出 sqlite3 异常
    """
    conn = sqlite3.connect(DB_PATH)
    # 从新表 paper_portfolio_positions 读取所有 open 持仓
    # 字段映射说明（旧表 position → 新表 paper_portfolio_positions）：
    #   rowid        → id            （主键，用于 UPDATE 定位）
    #   ts_code      → ticker        （股票代码）
    #   entry_price  → avg_cost      （成本价）
    #   shares       → quantity      （持仓数量）
    #   cost         → avg_cost * quantity （新表无此列，需计算得出）
    #   pnl/pnl_pct  → 存在 metadata_json.mark_to_market （新表无独立列）
    positions = conn.execute(
        """
        SELECT id, position_id, ticker, market, quantity, avg_cost, metadata_json
        FROM paper_portfolio_positions
        WHERE status='open'
        ORDER BY datetime(opened_at) DESC, id DESC
        """
    ).fetchall()

    total_pnl = 0
    updated = 0
    profitable = 0
    losing = 0
    for row_id, position_id, ticker, market, quantity, avg_cost, metadata_raw in positions:
        latest_price = fetch_latest_price(conn, ticker, market)
        if latest_price is None:
            print(f"  {ticker}: no price data")
            continue

        # 盈亏计算逻辑保持与原版一致
        # cost（成本总额）= 成本价 * 持仓数量（旧表有独立 cost 列，新表需要算出来）
        quantity_value = float(quantity or 0.0)
        avg_cost_value = float(avg_cost or 0.0)
        cost = avg_cost_value * quantity_value
        current_price = latest_price
        market_value = current_price * quantity_value
        pnl = market_value - cost
        pnl_pct = (current_price - avg_cost_value) / avg_cost_value if avg_cost_value > 0 else 0

        # 新表没有 pnl/pnl_pct 列，按 smr_paper_portfolio.py 的约定写进 metadata_json
        # 这样 mark_open_positions_to_market() 和 pnl.py 用同一套字段，数据流不冲突
        try:
            metadata = json.loads(metadata_raw) if metadata_raw else {}
        except json.JSONDecodeError:
            metadata = {}
        metadata["mark_to_market"] = {
            "latest_price": current_price,
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 4),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        conn.execute(
            "UPDATE paper_portfolio_positions SET metadata_json=? WHERE id=?",
            (json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str), row_id),
        )
        total_pnl += pnl
        updated += 1
        if pnl >= 0:
            profitable += 1
        else:
            losing += 1
        status = "📈" if pnl > 0 else "📉"
        print(f"  {status} {ticker}: PnL={pnl:+.2f} ({pnl_pct*100:+.2f}%) MV={market_value:.2f}")

    snapshot_date = os.environ.get("SMR_PNL_SNAPSHOT_DATE") or datetime.now().strftime("%Y-%m-%d")
    registry_entry = register_snapshot(
        conn,
        entity_type="portfolio_pnl_snapshot",
        entity_id=str(snapshot_date)[:10],
        status="updated" if updated else "empty",
        source="pnl.py",
        relationships={},
        payload={
            "open_position_count": len(positions),
            "updated_positions": updated,
            "profitable_positions": profitable,
            "losing_positions": losing,
            "total_pnl": round(total_pnl, 2),
        },
    )
    handoff_result = ensure_auto_handoff(
        conn,
        registry_entry,
        note="组合 PnL 快照已更新，必要时自动转交 Hermes-like 风险代理复盘。",
        created_by="pnl.py",
    )
    conn.commit()
    conn.close()
    log_run(
        "pnl.py",
        "success",
        "position pnl updated",
        {
            "updated_positions": updated,
            "total_pnl": round(total_pnl, 2),
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"\nUpdated {updated} positions, Total PnL: {total_pnl:+.2f}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
