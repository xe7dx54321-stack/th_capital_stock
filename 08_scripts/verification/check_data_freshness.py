#!/usr/bin/env python3
"""Check SMR market/factor freshness and coverage gaps."""

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_trade_calendar import expected_trade_dates, format_date, parse_date, trade_day_lag
from smr_runlog import log_run
from smr_universe import load_active_equity_universe, load_active_us_benchmarks

DB_PATH = project_path("01_data", "db", "smr.db")

TREND_FACTOR_NAMES = {
    "ma_20",
    "ma_60",
    "ma_120",
    "macd_dif",
    "macd_dea",
    "macd_hist",
    "trend_strength",
    "rsi_14",
    "volatility_20",
}
def latest_market_date(conn, market):
    row = conn.execute(
        "SELECT max(trade_date) FROM daily_bar WHERE market=?",
        (market,),
    ).fetchone()
    return parse_date(row[0] if row else None)


def latest_us_date(conn):
    row = conn.execute("SELECT max(trade_date) FROM us_daily_bar").fetchone()
    return parse_date(row[0] if row else None)


def latest_factor_date(conn, mode):
    if mode == "trend":
        placeholders = ",".join("?" for _ in TREND_FACTOR_NAMES)
        query = f"SELECT max(trade_date) FROM factor_daily WHERE factor_name IN ({placeholders})"
        row = conn.execute(query, tuple(sorted(TREND_FACTOR_NAMES))).fetchone()
    elif mode == "us_linkage":
        row = conn.execute(
            "SELECT max(trade_date) FROM factor_daily WHERE factor_name LIKE 'us_linkage_%'"
        ).fetchone()
    elif mode == "fundamental":
        placeholders = ",".join("?" for _ in TREND_FACTOR_NAMES)
        query = (
            "SELECT max(trade_date) FROM factor_daily "
            f"WHERE factor_name NOT IN ({placeholders}) "
            "AND factor_name NOT LIKE 'us_linkage_%'"
        )
        row = conn.execute(query, tuple(sorted(TREND_FACTOR_NAMES))).fetchone()
    else:
        raise ValueError(f"unsupported factor mode: {mode}")
    return parse_date(row[0] if row else None)


def business_day_lag(latest, expected):
    return trade_day_lag(latest, expected, "US")


def infer_expectations(now_dt, mode, expected_a_date=None, expected_hk_date=None, expected_us_date=None):
    inferred = expected_trade_dates(now_dt, mode=mode)
    return (
        expected_a_date or inferred["a_expected"],
        expected_hk_date or inferred["hk_expected"],
        expected_us_date or inferred["us_expected"],
        inferred["cn_factor_expected"],
    )


def latest_code_dates(conn, codes):
    result = {}
    for ts_code in codes:
        row = conn.execute(
            "SELECT max(trade_date) FROM daily_bar WHERE ts_code=?",
            (ts_code,),
        ).fetchone()
        result[ts_code] = parse_date(row[0] if row else None)
    return result


def build_status(latest, expected, market, coverage_missing_count=0):
    if latest is None:
        return "missing"
    lag = trade_day_lag(latest, expected, market)
    if lag and lag > 0:
        return "stale"
    if coverage_missing_count:
        return "warn"
    return "ok"


def main():
    parser = argparse.ArgumentParser(description="Check SMR market/factor freshness")
    parser.add_argument("--mode", choices=["status", "morning", "afternoon"], default="status")
    parser.add_argument("--as-of-date", help="Override local date with YYYY-MM-DD")
    parser.add_argument("--expected-cn-date", help="Expected latest A-share trade date")
    parser.add_argument("--expected-hk-date", help="Expected latest Hong Kong trade date")
    parser.add_argument("--expected-us-date", help="Expected latest US trade date")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when stale or missing")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    now_dt = datetime.now()
    if args.as_of_date:
        override_date = parse_date(args.as_of_date)
        now_dt = datetime.combine(override_date, now_dt.time())

    expected_a_date, expected_hk_date, expected_us_date, expected_cn_factor_date = infer_expectations(
        now_dt,
        args.mode,
        parse_date(args.expected_cn_date),
        parse_date(args.expected_hk_date),
        parse_date(args.expected_us_date),
    )

    conn = sqlite3.connect(DB_PATH)
    equity_universe = load_active_equity_universe(conn, include_seed=True)
    us_benchmarks = load_active_us_benchmarks(conn)

    a_codes = [code for code in equity_universe if code.endswith((".SZ", ".SH", ".BJ"))]
    hk_codes = [code for code in equity_universe if code.endswith(".HK")]
    a_code_dates = latest_code_dates(conn, a_codes)
    hk_code_dates = latest_code_dates(conn, hk_codes)

    checks = []
    latest_a = latest_market_date(conn, "A")
    latest_h = latest_market_date(conn, "H")
    latest_us = latest_us_date(conn)
    latest_trend = latest_factor_date(conn, "trend")
    latest_fundamental = latest_factor_date(conn, "fundamental")
    latest_linkage = latest_factor_date(conn, "us_linkage")

    def append_check(name, latest, expected, market, code_dates=None):
        missing_codes = sorted([code for code, value in (code_dates or {}).items() if value is None])
        checks.append(
            {
                "name": name,
                "latest_date": format_date(latest),
                "expected_date": format_date(expected),
                "lag_business_days": trade_day_lag(latest, expected, market),
                "coverage_missing_count": len(missing_codes),
                "coverage_missing_codes": missing_codes[:20],
                "status": build_status(latest, expected, market, len(missing_codes)),
            }
        )

    append_check("daily_bar_a", latest_a, expected_a_date, "A", a_code_dates)
    append_check("daily_bar_h", latest_h, expected_hk_date, "H", hk_code_dates)
    checks.append(
        {
            "name": "us_daily_bar",
            "latest_date": format_date(latest_us),
            "expected_date": format_date(expected_us_date),
            "lag_business_days": trade_day_lag(latest_us, expected_us_date, "US"),
            "coverage_missing_count": 0,
            "coverage_missing_codes": [],
            "benchmark_count": len(us_benchmarks),
            "status": build_status(latest_us, expected_us_date, "US", 0),
        }
    )
    checks.append(
        {
            "name": "trend_factor",
            "latest_date": format_date(latest_trend),
            "expected_date": format_date(expected_cn_factor_date),
            "lag_business_days": trade_day_lag(latest_trend, expected_cn_factor_date, "H"),
            "status": build_status(latest_trend, expected_cn_factor_date, "H", 0),
        }
    )
    checks.append(
        {
            "name": "fundamental_factor",
            "latest_date": format_date(latest_fundamental),
            "expected_date": format_date(expected_cn_factor_date),
            "lag_business_days": trade_day_lag(latest_fundamental, expected_cn_factor_date, "H"),
            "status": build_status(latest_fundamental, expected_cn_factor_date, "H", 0),
        }
    )
    checks.append(
        {
            "name": "us_linkage_factor",
            "latest_date": format_date(latest_linkage),
            "expected_date": format_date(expected_cn_factor_date),
            "lag_business_days": trade_day_lag(latest_linkage, expected_cn_factor_date, "H"),
            "status": build_status(latest_linkage, expected_cn_factor_date, "H", 0),
        }
    )
    conn.close()

    stale_or_missing = [
        item["name"]
        for item in checks
        if item["status"] in {"stale", "missing"}
    ]
    payload = {
        "mode": args.mode,
        "as_of_date": format_date(now_dt.date()),
        "expected_cn_date": format_date(expected_a_date),
        "expected_hk_date": format_date(expected_hk_date),
        "expected_cn_factor_date": format_date(expected_cn_factor_date),
        "expected_us_date": format_date(expected_us_date),
        "checks": checks,
        "stale_or_missing": stale_or_missing,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("SMR data freshness check")
        print(f"- mode: {args.mode}")
        print(f"- as_of_date: {payload['as_of_date']}")
        print(f"- expected_cn_date: {payload['expected_cn_date']}")
        print(f"- expected_hk_date: {payload['expected_hk_date']}")
        print(f"- expected_cn_factor_date: {payload['expected_cn_factor_date']}")
        print(f"- expected_us_date: {payload['expected_us_date']}")
        for item in checks:
            print(
                f"- {item['name']}: status={item['status']} "
                f"latest={item.get('latest_date') or ''} "
                f"expected={item.get('expected_date') or ''} "
                f"lag={item.get('lag_business_days')}"
            )
            if item.get("coverage_missing_count"):
                print(
                    f"  missing_codes={item['coverage_missing_count']} "
                    f"{','.join(item['coverage_missing_codes'])}"
                )

    log_run(
        "check_data_freshness.py",
        "success" if not stale_or_missing else "warning",
        "data freshness checked",
        payload,
    )

    if args.strict and stale_or_missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
