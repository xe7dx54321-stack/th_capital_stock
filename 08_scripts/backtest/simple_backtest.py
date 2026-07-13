#!/usr/bin/env python3
"""SMR Simple Backtest - Validates medium/long-term strategies on historical data."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 把同级的 lib 目录加入模块搜索路径，这样才能 import smr_paths
# 脚本位置：08_scripts/backtest/simple_backtest.py
# lib 位置：08_scripts/lib/
# 所以 parents[1]（即 08_scripts）再拼上 "lib" 就是 lib 目录
LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path

# 数据库路径：优先读环境变量 SMR_DB_PATH，否则用项目根目录下的 01_data/db/smr.db
# 这样无论是 macOS、Linux 还是 Windows 都能正确找到数据库
DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")

# 回测报告输出目录：优先读环境变量 SMR_REPORT_DIR，否则用项目根目录下的 04_portfolio/performance
REPORT_DIR = env_or_project_path("SMR_REPORT_DIR", "04_portfolio", "performance")


def run_momentum_backtest(conn, ts_code, ma_period=60, hold_days=20):
    """对单只股票跑一个简单的均线动量回测。

    用小白能懂的话说：这只股票过去 N 天（ma_period）的平均价叫均线，
    如果今天的收盘价高于均线，就认为是上涨趋势，"买入"；
    然后持有 hold_days 天后卖出，看看是赚还是亏。
    最后统计所有这样"买入-持有"的交易的胜率、平均收益等指标。

    参数:
        conn (sqlite3.Connection): 已经打开的 SQLite 数据库连接，用来查行情数据。
        ts_code (str): 股票代码，比如 "300308.SZ"。
        ma_period (int): 均线周期，默认 60 天，也就是用过去 60 天的收盘价算平均。
        hold_days (int): 持有天数，默认 20 天，买入后持有这么久再卖出。

    返回值:
        dict: 包含回测指标的字典，字段有：
            - ts_code: 股票代码
            - strategy: 策略名称（形如 "MA60_momentum_hold20d"）
            - total_trades: 总交易次数
            - win_rate: 胜率（0~1 之间的小数，0.6 表示 60%）
            - avg_return: 平均每笔交易的收益率
            - profit_factor: 盈亏比（平均盈利 / 平均亏损）
            - avg_win: 平均每笔盈利交易的收益率
            - avg_loss: 平均每笔亏损交易的收益率（绝对值）
        如果数据不够（少于 ma_period + hold_days 天）或者没有有效交易，返回 None。

    异常处理:
        函数本身不主动抛异常。如果数据库查询失败，异常会向上抛给调用者。
        数据不足或无交易时通过返回 None 来表示"无法回测"，由调用者判断。
    """
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
    """回测脚本的入口函数：解析命令行参数，跑回测，生成 Markdown 报告。

    用小白能懂的话说：这个函数负责"接活"——
    1. 看看用户在命令行里输入了什么参数（哪只股票、均线多少天、持有多少天）；
    2. 打开数据库，对指定的股票（或所有股票）逐个跑回测；
    3. 把每只股票的回测结果打印到屏幕上；
    4. 最后把所有结果整理成一份 Markdown 表格报告，存到报告目录里。

    参数:
        无（从命令行 sys.argv 读取，通过 argparse 解析）。
        支持的命令行参数：
            --ts-code: 指定单只股票代码，比如 --ts-code 300308.SZ
            --ma: 均线周期，默认 60
            --hold: 持有天数，默认 20
            --all: 对数据库里所有有数据的股票都跑一遍回测

    返回值:
        无（直接打印结果到屏幕，并把报告写到文件）。

    异常处理:
        如果既没指定 --ts-code 也没指定 --all，会打印提示并直接返回。
        如果数据库连接失败，异常会向上抛出（这里不捕获，让用户看到真实错误）。
    """
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
