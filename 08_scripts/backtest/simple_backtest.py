#!/usr/bin/env python3
"""SMR Simple Backtest - Validates medium/long-term strategies on historical data."""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db")
REPORT_DIR = Path("/Users/apple/Documents/同行资本二级市场/04_portfolio/performance")


def run_momentum_backtest(conn, ts_code, ma_period=60, hold_days=20):
    import pandas as pd
    df = pd.read_sql(
        "SELECT trade_date, close FROM daily_bar WHERE ts_code=? ORDER BY trade_date",
        conn, params=(ts_code,),
    )
    if len(df) < ma_period + hold_days:
        return None

    df["ma"] = df["close"].rolling(ma_period).mean()
    df["signal"] = (df["close"] > df["ma"]).astype(int)
    df["future_return"] = df["close"].pct_change(hold_days).shift(-hold_days)

    trades = df[df["signal"] == 1].dropna(subset=["future_return"])
    if len(trades) == 0:
        return None

    win_rate = (trades["future_return"] > 0).mean()
    avg_return = trades["future_return"].mean()
    total_trades = len(trades)
    avg_win = trades[trades["future_return"] > 0]["future_return"].mean() if win_rate > 0 else 0
    avg_loss = abs(trades[trades["future_return"] <= 0]["future_return"].mean()) if (1 - win_rate) > 0 else 0.01
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float("inf")

    return {
        "ts_code": ts_code,
        "strategy": f"MA{ma_period}_momentum_hold{hold_days}d",
        "total_trades": total_trades,
        "win_rate": round(win_rate, 4),
        "avg_return": round(avg_return, 4),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="SMR Simple Backtest")
    parser.add_argument("--ts-code", help="Specific stock code")
    parser.add_argument("--ma", type=int, default=60, help="MA period")
    parser.add_argument("--hold", type=int, default=20, help="Holding days")
    parser.add_argument("--all", action="store_true", help="Run for all stocks with data")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.ts_code:
        codes = [args.ts_code]
    elif args.all:
        codes = [r[0] for r in conn.execute("SELECT DISTINCT ts_code FROM daily_bar").fetchall()]
    else:
        print("Specify --ts-code or --all")
        return

    results = []
    for code in codes:
        r = run_momentum_backtest(conn, code, args.ma, args.hold)
        if r:
            results.append(r)
            print(f"  {r['ts_code']:12s} trades={r['total_trades']:3d} win={r['win_rate']:.1%} avg_ret={r['avg_return']:.2%} pf={r['profit_factor']:.2f}")

    conn.close()

    if results:
        report_path = REPORT_DIR / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Backtest Report - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"Strategy: MA{args.ma} momentum, hold {args.hold} days\n\n")
            f.write("| Stock | Trades | Win Rate | Avg Return | Profit Factor |\n")
            f.write("|-------|--------|----------|------------|---------------|\n")
            for r in sorted(results, key=lambda x: x["avg_return"], reverse=True):
                f.write(f"| {r['ts_code']} | {r['total_trades']} | {r['win_rate']:.1%} | {r['avg_return']:.2%} | {r['profit_factor']:.2f} |\n")
        print(f"\nReport saved to {report_path}")
    else:
        print("No valid backtest results")


if __name__ == "__main__":
    main()
