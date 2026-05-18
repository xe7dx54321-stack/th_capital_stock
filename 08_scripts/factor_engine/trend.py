#!/usr/bin/env python3
"""SMR Trend Factor Calculator - Computes medium/long-term trend factors."""

import argparse
import math
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")


def batch_entity_id(ts_code):
    if ts_code:
        return f"ts_code__{ts_code}"
    return "all_equities"


def mean(values):
    return sum(values) / len(values)


def sample_std(values):
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def ema(values, span):
    if not values:
        return []
    alpha = 2 / (span + 1)
    results = [values[0]]
    for value in values[1:]:
        results.append(alpha * value + (1 - alpha) * results[-1])
    return results


def rolling_mean(values, period):
    if len(values) < period:
        return None
    return mean(values[-period:])


def compute_ma_factors(closes, periods=(20, 60, 120)):
    results = []
    for p in periods:
        ma_val = rolling_mean(closes, p)
        if ma_val is not None:
            results.append(("ma_" + str(p), round(ma_val, 4)))
    return results


def compute_macd_factor(closes):
    if len(closes) < 35:
        return []
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    dif = [value12 - value26 for value12, value26 in zip(ema12, ema26)]
    dea = ema(dif, 9)
    macd = [(dif_value - dea_value) * 2 for dif_value, dea_value in zip(dif, dea)]
    return [
        ("macd_dif", round(dif[-1], 4)),
        ("macd_dea", round(dea[-1], 4)),
        ("macd_hist", round(macd[-1], 4)),
    ]


def compute_trend_strength(closes):
    if len(closes) < 20:
        return []
    ma20 = rolling_mean(closes, 20)
    ma60 = rolling_mean(closes, 60) if len(closes) >= 60 else None
    close = closes[-1]
    score = 0
    if ma20 is not None and ma20 > 0:
        if close > ma20:
            score += 1
    if ma60 is not None and ma60 > 0:
        if close > ma60:
            score += 1
        if ma20 > ma60:
            score += 1
    return [("trend_strength", score)]


def compute_rsi_factor(closes, period=14):
    if len(closes) < period + 1:
        return []
    deltas = [current - previous for previous, current in zip(closes[:-1], closes[1:])]
    recent = deltas[-period:]
    gain = mean([delta if delta > 0 else 0 for delta in recent])
    loss = mean([-delta if delta < 0 else 0 for delta in recent])
    rs = gain / (loss or 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return [("rsi_" + str(period), round(rsi, 2))]


def compute_volatility_factor(closes, period=20):
    if len(closes) < period + 1:
        return []
    returns = []
    for previous, current in zip(closes[:-1], closes[1:]):
        if previous in (None, 0):
            continue
        returns.append(current / previous - 1)
    if len(returns) < period:
        return []
    vol = sample_std(returns[-period:]) * (252 ** 0.5)
    return [("volatility_" + str(period), round(vol, 4))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ts-code", help="Specific stock code to process")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.ts_code:
        codes = [args.ts_code]
    else:
        codes = [r[0] for r in conn.execute("SELECT DISTINCT ts_code FROM daily_bar").fetchall()]

    total = 0
    processed = 0
    factor_names = set()
    processed_trade_dates = set()
    for code in codes:
        rows = conn.execute(
            "SELECT trade_date, close FROM daily_bar WHERE ts_code=? ORDER BY trade_date",
            (code,),
        ).fetchall()
        if len(rows) < 5:
            continue
        closes = [row[1] for row in rows if row[1] is not None]
        if len(closes) < 5:
            continue

        all_factors = []
        all_factors.extend(compute_ma_factors(closes))
        all_factors.extend(compute_macd_factor(closes))
        all_factors.extend(compute_trend_strength(closes))
        all_factors.extend(compute_rsi_factor(closes))
        all_factors.extend(compute_volatility_factor(closes))

        trade_date = rows[-1][0]
        for fname, fval in all_factors:
            conn.execute(
                "INSERT OR REPLACE INTO factor_daily (ts_code, trade_date, factor_name, factor_value) VALUES (?, ?, ?, ?)",
                (code, trade_date, fname, fval),
            )
            factor_names.add(fname)
        total += len(all_factors)
        processed += 1
        processed_trade_dates.add(trade_date)

    register_snapshot(
        conn,
        entity_type="trend_factor_snapshot",
        entity_id=batch_entity_id(args.ts_code),
        status="computed" if total else "empty",
        source="trend.py",
        relationships={"ts_code_filter": args.ts_code},
        payload={
            "requested_code": args.ts_code,
            "processed_codes": processed,
            "factor_count": total,
            "factor_names": sorted(factor_names),
            "latest_trade_dates": sorted(processed_trade_dates),
        },
    )
    conn.commit()
    conn.close()
    log_run(
        "trend.py",
        "success",
        "trend factors computed",
        {
            "requested_code": args.ts_code,
            "processed_codes": processed,
            "factor_count": total,
        },
    )
    print(f"Computed {total} trend factors for {len(codes)} stocks")


if __name__ == "__main__":
    main()
