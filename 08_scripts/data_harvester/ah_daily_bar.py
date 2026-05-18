#!/usr/bin/env python3
"""SMR A+H Daily Bar Harvester - Collects daily OHLCV data for SMR universe stocks."""

import argparse
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import register_snapshot
from smr_universe import load_active_equity_universe, load_active_us_benchmarks, split_ts_code
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
LOG_DIR = project_path("10_logs")


def latest_trade_date(conn, table_name):
    row = conn.execute(f"SELECT max(trade_date) FROM {table_name}").fetchone()
    return row[0] if row else None


def latest_trade_date_for_symbol(conn, table_name, column_name, symbol):
    row = conn.execute(
        f"SELECT max(trade_date) FROM {table_name} WHERE {column_name}=?",
        (symbol,),
    ).fetchone()
    return row[0] if row else None


def parse_trade_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def effective_days_to_fetch(latest_trade_date_value, requested_days, overlap_days=2):
    latest_dt = parse_trade_date(latest_trade_date_value)
    if latest_dt is None:
        return requested_days
    today = datetime.now().date()
    gap_days = max(0, (today - latest_dt).days + overlap_days)
    return max(requested_days, gap_days)


def infer_cn_exchange(code):
    if code.startswith(("0", "3")):
        return "sz", "SZ"
    if code.startswith(("4", "8")):
        return "bj", "BJ"
    return "sh", "SH"


def safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_pct_change(close_value, prev_close):
    close_num = safe_float(close_value)
    prev_num = safe_float(prev_close)
    if close_num is None or prev_num in (None, 0):
        return None
    return round((close_num - prev_num) / prev_num * 100, 4)


def normalize_a_history_rows(df, code, market_suffix, start_date):
    if df is None or df.empty:
        return []

    df = df.copy()
    column_names = set(df.columns)
    if "date" in column_names:
        date_col = "date"
        open_col = "open"
        close_col = "close"
        high_col = "high"
        low_col = "low"
        vol_col = "amount"
        amount_col = None
        pct_col = None
        turnover_col = None
    elif "日期" in column_names:
        date_col = "日期"
        open_col = "开盘"
        close_col = "收盘"
        high_col = "最高"
        low_col = "最低"
        vol_col = "成交量"
        amount_col = "成交额"
        pct_col = "涨跌幅"
        turnover_col = "换手率"
    else:
        raise RuntimeError(f"unsupported_a_history_columns:{sorted(column_names)}")

    df[date_col] = df[date_col].astype(str)
    df = df[df[date_col] >= start_date.strftime("%Y-%m-%d")]
    rows = []
    prev_close = None
    for _, r in df.iterrows():
        close_value = safe_float(r[close_col])
        pct_chg = safe_float(r[pct_col]) if pct_col else None
        if pct_chg is None:
            pct_chg = compute_pct_change(close_value, prev_close)
        rows.append(
            {
                "ts_code": f"{code}.{market_suffix}",
                "trade_date": str(r[date_col]),
                "open": safe_float(r[open_col]),
                "close": close_value,
                "high": safe_float(r[high_col]),
                "low": safe_float(r[low_col]),
                "vol": safe_float(r[vol_col]) if vol_col else None,
                "amount": safe_float(r[amount_col]) if amount_col else None,
                "pct_chg": pct_chg,
                "turnover": safe_float(r[turnover_col]) if turnover_col else None,
                "market": "A",
            }
        )
        prev_close = close_value
    return rows


def fetch_a_stock_history(code, days=30):
    import akshare as ak

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 10)
    market_prefix, market_suffix = infer_cn_exchange(code)
    providers = []
    if market_suffix != "BJ":
        providers.append(
            (
                "tencent",
                lambda: ak.stock_zh_a_hist_tx(
                    symbol=market_prefix + code,
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="qfq",
                ),
            )
        )
    providers.append(
        (
            "eastmoney",
            lambda: ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            ),
        )
    )

    errors = []
    for provider_name, loader in providers:
        try:
            rows = normalize_a_history_rows(with_requests_timeout(loader), code, market_suffix, start_date)
            if rows:
                return rows
            errors.append(f"{provider_name}:empty")
        except Exception as exc:
            errors.append(f"{provider_name}:{exc}")

    error_summary = "; ".join(errors) or "no_provider_attempted"
    raise RuntimeError(f"a_history_unavailable:{code}.{market_suffix}:{error_summary}")


def with_requests_timeout(loader: Callable[[], object], timeout_seconds: float = 20.0):
    import requests

    original_get = requests.get

    def wrapped_get(*args, **kwargs):
        kwargs.setdefault("timeout", timeout_seconds)
        return original_get(*args, **kwargs)

    requests.get = wrapped_get
    try:
        return loader()
    finally:
        requests.get = original_get


def fetch_hk_stock_history(code, days=30):
    import akshare as ak
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 10)
    df = with_requests_timeout(lambda: ak.stock_hk_daily(symbol=code, adjust="qfq"))
    df = df.copy()
    df["date"] = df["date"].astype(str)
    df = df[df["date"] >= start_date.strftime("%Y-%m-%d")]
    rows = []
    prev_close = None
    for _, r in df.iterrows():
        close_value = safe_float(r["close"])
        rows.append({
            "ts_code": code + ".HK",
            "trade_date": str(r["date"]),
            "open": safe_float(r["open"]),
            "close": close_value,
            "high": safe_float(r["high"]),
            "low": safe_float(r["low"]),
            "vol": safe_float(r["volume"]),
            "amount": safe_float(r["amount"]),
            "pct_chg": compute_pct_change(close_value, prev_close),
            "turnover": None,
            "market": "H",
        })
        prev_close = close_value
    return rows


def fetch_us_stock_history(symbol, days=30):
    import akshare as ak
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 10)
    df = with_requests_timeout(lambda: ak.stock_us_daily(symbol=symbol, adjust="qfq"))
    df = df.copy()
    df["date"] = df["date"].astype(str)
    df = df[df["date"] >= start_date.strftime("%Y-%m-%d")]
    rows = []
    prev_close = None
    for _, r in df.iterrows():
        close_value = safe_float(r["close"])
        rows.append({
            "symbol": symbol,
            "trade_date": str(r["date"]),
            "open": safe_float(r["open"]),
            "close": close_value,
            "high": safe_float(r["high"]),
            "low": safe_float(r["low"]),
            "vol": safe_float(r["volume"]),
            "amount": 0.0,
            "pct_chg": compute_pct_change(close_value, prev_close),
        })
        prev_close = close_value
    return rows


def normalize_target_code(raw_value):
    value = (raw_value or "").strip().upper()
    if not value:
        raise ValueError("empty ts-code")
    if "." in value:
        code, market = value.split(".", 1)
        market = market.upper()
        if market in {"SZ", "SH", "BJ", "HK"}:
            return f"{code}.{market}"
        return value
    if value.isalpha():
        return value
    if len(value) == 5 and value.startswith("0"):
        return f"{value}.HK"
    if value.startswith(("0", "3")):
        return f"{value}.SZ"
    if value.startswith(("4", "8")):
        return f"{value}.BJ"
    return f"{value}.SH"


def insert_daily_bars(conn, rows):
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""INSERT OR REPLACE INTO daily_bar
                (ts_code, trade_date, open, close, high, low, vol, amount, pct_chg, turnover, market)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["ts_code"], r["trade_date"], r["open"], r["close"], r["high"],
                 r["low"], r["vol"], r["amount"], r["pct_chg"], r["turnover"], r["market"]))
            inserted += 1
        except Exception as e:
            print(f"    Error inserting {r['ts_code']} {r['trade_date']}: {e}")
    return inserted


def insert_us_daily_bars(conn, rows):
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""INSERT OR REPLACE INTO us_daily_bar
                (symbol, trade_date, open, close, high, low, vol, amount, pct_chg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["symbol"], r["trade_date"], r["open"], r["close"], r["high"],
                 r["low"], r["vol"], r["amount"], r["pct_chg"]))
            inserted += 1
        except Exception as e:
            print(f"    Error inserting {r['symbol']} {r['trade_date']}: {e}")
    return inserted


def main():
    parser = argparse.ArgumentParser(description="SMR A+H Daily Bar Harvester")
    parser.add_argument("--days", type=int, default=30, help="Number of days to fetch")
    parser.add_argument("--a-only", action="store_true", help="Only fetch A-shares")
    parser.add_argument("--hk-only", action="store_true", help="Only fetch H-shares")
    parser.add_argument("--us-only", action="store_true", help="Only fetch US benchmarks")
    parser.add_argument("--ts-code", action="append", help="Specific A/H ts_code or raw code; can be repeated")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    total_inserted = 0
    equity_universe = load_active_equity_universe(conn, include_seed=True)
    us_benchmarks = load_active_us_benchmarks(conn)

    if args.ts_code:
        filtered_equity_universe = {}
        filtered_us_benchmarks = {}
        for raw_value in args.ts_code:
            target_code = normalize_target_code(raw_value)
            if target_code in us_benchmarks:
                filtered_us_benchmarks[target_code] = us_benchmarks[target_code]
                continue
            meta = equity_universe.get(target_code, {})
            filtered_equity_universe[target_code] = {
                "name": meta.get("name", target_code),
                "sector": meta.get("sector"),
                "market": meta.get("market", split_ts_code(target_code)[1]),
                "source_pool_types": meta.get("source_pool_types", []),
            }
        equity_universe = filtered_equity_universe
        us_benchmarks = filtered_us_benchmarks

    a_stocks = {}
    hk_stocks = {}
    market_inserted = {"A": 0, "H": 0, "US": 0}
    failures = []
    lookback_by_market = {"A": {}, "H": {}, "US": {}}
    for ts_code, meta in equity_universe.items():
        code, market = split_ts_code(ts_code)
        if market in {"SZ", "SH", "BJ"}:
            a_stocks[code] = meta["name"]
        elif market == "HK":
            hk_stocks[code] = meta["name"]

    if not args.us_only and not args.hk_only:
        print(f"[A-Share] Fetching {len(a_stocks)} stocks, {args.days} days...")
        for code, name in a_stocks.items():
            try:
                ts_code = f"{code}.{infer_cn_exchange(code)[1]}"
                fetch_days = effective_days_to_fetch(
                    latest_trade_date_for_symbol(conn, "daily_bar", "ts_code", ts_code),
                    args.days,
                )
                lookback_by_market["A"][ts_code] = fetch_days
                rows = fetch_a_stock_history(code, fetch_days)
                n = insert_daily_bars(conn, rows)
                total_inserted += n
                market_inserted["A"] += n
                print(f"  {code} {name}: {n} bars (lookback={fetch_days}d)")
                time.sleep(0.5)
            except Exception as e:
                failures.append({"symbol": ts_code, "market": "A", "error": str(e)})
                print(f"  {code} {name}: ERROR - {e}")
                time.sleep(1)

    if not args.us_only and not args.a_only:
        print(f"\n[H-Share] Fetching {len(hk_stocks)} stocks, {args.days} days...")
        for code, name in hk_stocks.items():
            try:
                ts_code = f"{code}.HK"
                fetch_days = effective_days_to_fetch(
                    latest_trade_date_for_symbol(conn, "daily_bar", "ts_code", ts_code),
                    args.days,
                )
                lookback_by_market["H"][ts_code] = fetch_days
                rows = fetch_hk_stock_history(code, fetch_days)
                n = insert_daily_bars(conn, rows)
                total_inserted += n
                market_inserted["H"] += n
                print(f"  {code} {name}: {n} bars (lookback={fetch_days}d)")
                time.sleep(0.5)
            except Exception as e:
                failures.append({"symbol": f"{code}.HK", "market": "H", "error": str(e)})
                print(f"  {code} {name}: ERROR - {e}")
                time.sleep(1)

    if not args.a_only and not args.hk_only:
        print(f"\n[US] Fetching {len(us_benchmarks)} benchmarks, {args.days} days...")
        for symbol, meta in us_benchmarks.items():
            name = meta["name"]
            try:
                fetch_days = effective_days_to_fetch(
                    latest_trade_date_for_symbol(conn, "us_daily_bar", "symbol", symbol),
                    args.days,
                )
                lookback_by_market["US"][symbol] = fetch_days
                rows = fetch_us_stock_history(symbol, fetch_days)
                n = insert_us_daily_bars(conn, rows)
                total_inserted += n
                market_inserted["US"] += n
                print(f"  {symbol} {name}: {n} bars (lookback={fetch_days}d)")
                time.sleep(1)
            except Exception as e:
                failures.append({"symbol": symbol, "market": "US", "error": str(e)})
                print(f"  {symbol} {name}: ERROR - {e}")
                time.sleep(2)

    execution_date = datetime.now().strftime("%Y-%m-%d")
    register_snapshot(
        conn,
        entity_type="market_data_harvest",
        entity_id=execution_date,
        status="harvested" if total_inserted else "empty",
        source="ah_daily_bar.py",
        relationships={
            "a_only": args.a_only,
            "hk_only": args.hk_only,
            "us_only": args.us_only,
            "requested_ts_codes": args.ts_code or [],
        },
        payload={
            "days": args.days,
            "total_inserted": total_inserted,
            "by_market": market_inserted,
            "lookback_by_market": lookback_by_market,
            "failed_count": len(failures),
            "failed_symbols": failures[:20],
            "equity_universe_size": len(equity_universe),
            "us_benchmark_size": len(us_benchmarks),
            "latest_ah_trade_date": latest_trade_date(conn, "daily_bar"),
            "latest_us_trade_date": latest_trade_date(conn, "us_daily_bar"),
        },
    )
    conn.commit()
    conn.close()
    log_run(
        "ah_daily_bar.py",
        "success",
        "daily bars harvested",
        {
            "total_inserted": total_inserted,
            "by_market": market_inserted,
            "days": args.days,
            "failed_count": len(failures),
        },
    )
    print(f"\nTotal inserted: {total_inserted} bars")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
