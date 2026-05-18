#!/usr/bin/env python3
"""SMR PnL Calculator - Updates P&L for all open positions."""

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


def main():
    conn = sqlite3.connect(DB_PATH)
    positions = conn.execute(
        "SELECT rowid, ts_code, entry_price, shares, cost FROM position WHERE status='open'"
    ).fetchall()

    total_pnl = 0
    updated = 0
    profitable = 0
    losing = 0
    for rowid, ts_code, entry_price, shares, cost in positions:
        latest = conn.execute(
            "SELECT close FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ts_code,),
        ).fetchone()
        if not latest:
            print(f"  {ts_code}: no price data")
            continue

        current_price = latest[0]
        market_value = current_price * shares
        pnl = market_value - cost
        pnl_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0

        conn.execute(
            "UPDATE position SET pnl=?, pnl_pct=? WHERE rowid=?",
            (round(pnl, 2), round(pnl_pct, 4), rowid),
        )
        total_pnl += pnl
        updated += 1
        if pnl >= 0:
            profitable += 1
        else:
            losing += 1
        status = "📈" if pnl > 0 else "📉"
        print(f"  {status} {ts_code}: PnL={pnl:+.2f} ({pnl_pct*100:+.2f}%) MV={market_value:.2f}")

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
