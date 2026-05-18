#!/usr/bin/env python3
"""SMR US-AH Linkage Factor Calculator - Computes cross-market momentum传导 factors."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe, load_active_us_benchmarks, load_sector_benchmark_map

DB_PATH = project_path("01_data", "db", "smr.db")


def compute_linkage_factor(conn, us_symbol, ah_codes, lookback=5):
    us_rows = conn.execute(
        "SELECT trade_date, pct_chg FROM us_daily_bar WHERE symbol=? ORDER BY trade_date DESC LIMIT ?",
        (us_symbol, lookback + 5),
    ).fetchall()
    if len(us_rows) < 2:
        return []

    us_momentum = sum((row[1] or 0.0) for row in us_rows[:lookback])

    results = []
    for ah_code in ah_codes:
        ah_rows = conn.execute(
            "SELECT trade_date, pct_chg FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT ?",
            (ah_code, lookback + 5),
        ).fetchall()
        if len(ah_rows) < 2:
            continue
        ah_momentum = sum((row[1] or 0.0) for row in ah_rows[:lookback])
        linkage_score = round(us_momentum * 0.3 + ah_momentum * 0.7, 4)
        trade_date = ah_rows[0][0]
        results.append((ah_code, trade_date, linkage_score))

    return results


def main():
    conn = sqlite3.connect(DB_PATH)
    total = 0
    counts_by_sector = {}
    processed_trade_dates = set()
    used_benchmarks = set()
    equity_universe = load_active_equity_universe(conn, include_seed=True)
    active_us_benchmarks = load_active_us_benchmarks(conn)
    sector_benchmark_map = load_sector_benchmark_map(conn)

    sector_equity_map = {}
    for ts_code, meta in equity_universe.items():
        sector_equity_map.setdefault(meta["sector"], []).append(ts_code)

    for sector, ah_codes in sector_equity_map.items():
        for us_symbol in sector_benchmark_map.get(sector, []):
            if us_symbol not in active_us_benchmarks:
                continue
            results = compute_linkage_factor(conn, us_symbol, ah_codes)
            if results:
                for ah_code, trade_date, score in results:
                    conn.execute(
                        "INSERT OR REPLACE INTO factor_daily (ts_code, trade_date, factor_name, factor_value) VALUES (?, ?, ?, ?)",
                        (ah_code, trade_date, f"us_linkage_{us_symbol.lower()}", score),
                    )
                    total += 1
                    counts_by_sector[sector] = counts_by_sector.get(sector, 0) + 1
                    processed_trade_dates.add(trade_date)
                    used_benchmarks.add(us_symbol)
                print(f"  {sector}: {us_symbol} -> {len(results)} stocks linked")
            else:
                print(f"  {sector}: {us_symbol} insufficient data")

    latest_trade_date = max(processed_trade_dates) if processed_trade_dates else None
    register_snapshot(
        conn,
        entity_type="us_linkage_factor_snapshot",
        entity_id=latest_trade_date or "all_sectors",
        status="computed" if total else "empty",
        source="us_linkage.py",
        relationships={
            "sector_count": len(sector_equity_map),
            "active_us_benchmark_count": len(active_us_benchmarks),
        },
        payload={
            "linked_factor_count": total,
            "counts_by_sector": counts_by_sector,
            "benchmarks_used": sorted(used_benchmarks),
            "latest_trade_dates": sorted(processed_trade_dates),
        },
    )
    conn.commit()
    conn.close()
    log_run(
        "us_linkage.py",
        "success",
        "us linkage factors computed",
        {
            "linked_factor_count": total,
            "counts_by_sector": counts_by_sector,
            "benchmarks_used": sorted(used_benchmarks),
        },
    )
    print(f"Computed {total} linkage factors")


if __name__ == "__main__":
    main()
