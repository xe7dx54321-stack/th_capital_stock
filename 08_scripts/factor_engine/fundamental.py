#!/usr/bin/env python3
"""SMR Fundamental Factor Calculator - Computes snapshot and lightweight financial factors."""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe, split_ts_code

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")


def batch_entity_id(code):
    if code:
        return f"code__{code}"
    return "all_equities"


def safe_float(value):
    if value in (None, "", "None", "False", False, "nan", "-", "--"):
        return None
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("%", "").replace("万", "").replace("亿", "").strip()
        if cleaned in ("", "False"):
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_scaled_amount(value):
    if value in (None, "", "None", "False", False, "nan", "-", "--"):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "").strip()
    multiplier = 1.0
    if text.endswith("亿"):
        multiplier = 1e8
        text = text[:-1]
    elif text.endswith("万"):
        multiplier = 1e4
        text = text[:-1]

    try:
        return float(text) * multiplier
    except ValueError:
        return None


def to_xq_symbol(code):
    return ("SZ" if code.startswith(("0", "3")) else "SH") + code


def to_ts_code(code, market=None):
    if market == "HK":
        return f"{code}.HK"
    if market == "BJ":
        return f"{code}.BJ"
    if market == "SZ":
        return f"{code}.SZ"
    if market == "SH":
        return f"{code}.SH"
    return f"{code}.SZ" if code.startswith(("0", "3")) else f"{code}.SH"


def fetch_snapshot_a(code):
    import akshare as ak

    df = ak.stock_individual_spot_xq(symbol=to_xq_symbol(code))
    return dict(zip(df["item"], df["value"]))


def fetch_financial_abstract_a(code):
    import akshare as ak

    df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
    if df.empty:
        return {}
    latest = df.iloc[-1].to_dict()
    return latest


def fetch_financial_indicator_hk(code):
    import akshare as ak

    df = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
    if df.empty:
        return {}
    latest = df.iloc[0].to_dict()
    return latest


def build_spot_factors_a(info):
    price = safe_float(info.get("现价"))
    total_shares = safe_float(info.get("基金份额/总股本")) or safe_float(info.get("总股本"))
    float_shares = safe_float(info.get("流通股"))
    pe_ttm = safe_float(info.get("市盈率(TTM)"))
    pe_dynamic = safe_float(info.get("市盈率(动)"))
    pe_static = safe_float(info.get("市盈率(静)"))
    pb = safe_float(info.get("市净率"))
    eps = safe_float(info.get("每股收益"))
    bvps = safe_float(info.get("每股净资产"))
    dividend_yield = safe_float(info.get("股息率(TTM)"))
    turnover = safe_float(info.get("周转率"))
    ytd_return = safe_float(info.get("今年以来涨幅"))
    high_52w = safe_float(info.get("52周最高"))
    low_52w = safe_float(info.get("52周最低"))
    goodwill_ratio = safe_float(info.get("净资产中的商誉"))

    factors = []
    if price is not None and total_shares is not None:
        factors.append(("market_cap", round(price * total_shares / 1e8, 2)))
    if price is not None and float_shares is not None:
        factors.append(("float_market_cap", round(price * float_shares / 1e8, 2)))
    if pe_ttm is not None:
        factors.append(("pe_ttm", round(pe_ttm, 4)))
    if pe_dynamic is not None:
        factors.append(("pe_dynamic", round(pe_dynamic, 4)))
    if pe_static is not None:
        factors.append(("pe_static", round(pe_static, 4)))
    if pb is not None:
        factors.append(("pb", round(pb, 4)))
    if eps is not None:
        factors.append(("eps_ttm", round(eps, 4)))
    if bvps is not None:
        factors.append(("book_value_per_share", round(bvps, 4)))
    if eps is not None and bvps not in (None, 0):
        factors.append(("roe_est", round(eps / bvps * 100, 4)))
    if dividend_yield is not None:
        factors.append(("dividend_yield_ttm", round(dividend_yield, 4)))
    if turnover is not None:
        factors.append(("turnover_week", round(turnover, 4)))
    if ytd_return is not None:
        factors.append(("ytd_return", round(ytd_return, 4)))
    if price is not None and high_52w not in (None, 0):
        factors.append(("pct_to_52w_high", round(price / high_52w * 100, 4)))
    if price is not None and low_52w not in (None, 0):
        factors.append(("pct_to_52w_low", round(price / low_52w * 100, 4)))
    if goodwill_ratio is not None:
        factors.append(("goodwill_to_net_asset_ratio", round(goodwill_ratio, 6)))
    return factors


def build_financial_factors_a(info):
    amount_mapping = {
        "revenue": "营业总收入",
        "net_profit": "净利润",
        "ex_profit": "扣非净利润",
    }
    mapping = {
        "revenue_yoy": "营业总收入同比增长率",
        "net_profit_yoy": "净利润同比增长率",
        "ex_profit_yoy": "扣非净利润同比增长率",
        "gross_margin": "销售毛利率",
        "net_margin": "销售净利率",
        "roe_reported": "净资产收益率",
        "roe_diluted": "净资产收益率-摊薄",
        "debt_asset_ratio": "资产负债率",
        "current_ratio": "流动比率",
        "quick_ratio": "速动比率",
        "ocf_per_share": "每股经营现金流",
        "basic_eps_reported": "基本每股收益",
        "bps_reported": "每股净资产",
        "inventory_turnover_days": "存货周转天数",
        "ar_turnover_days": "应收账款周转天数",
        "equity_ratio": "产权比率",
    }
    factors = []
    for factor_name, source_key in amount_mapping.items():
        value = parse_scaled_amount(info.get(source_key))
        if value is not None:
            factors.append((factor_name, round(value, 2)))
    for factor_name, source_key in mapping.items():
        value = safe_float(info.get(source_key))
        if value is not None:
            factors.append((factor_name, round(value, 4)))
    return factors


def build_financial_factors_hk(info):
    amount_mapping = {
        "revenue": "OPERATE_INCOME",
        "gross_profit": "GROSS_PROFIT",
        "holder_profit": "HOLDER_PROFIT",
    }
    mapping = {
        "revenue_yoy": "OPERATE_INCOME_YOY",
        "net_profit_yoy": "HOLDER_PROFIT_YOY",
        "gross_margin": "GROSS_PROFIT_RATIO",
        "net_margin": "NET_PROFIT_RATIO",
        "roe_reported": "ROE_AVG",
        "debt_asset_ratio": "DEBT_ASSET_RATIO",
        "current_ratio": "CURRENT_RATIO",
        "basic_eps_reported": "BASIC_EPS",
        "bps_reported": "BPS",
        "ocf_per_share": "PER_NETCASH_OPERATE",
        "eps_ttm": "EPS_TTM",
        "revenue_qoq": "OPERATE_INCOME_QOQ",
        "gross_profit_qoq": "GROSS_PROFIT_QOQ",
        "holder_profit_qoq": "HOLDER_PROFIT_QOQ",
        "roa": "ROA",
    }
    factors = []
    for factor_name, source_key in amount_mapping.items():
        value = safe_float(info.get(source_key))
        if value is not None:
            factors.append((factor_name, round(value, 2)))
    for factor_name, source_key in mapping.items():
        value = safe_float(info.get(source_key))
        if value is not None:
            factors.append((factor_name, round(value, 4)))
    return factors


def latest_trade_date(conn, ts_code):
    row = conn.execute(
        "SELECT trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    ).fetchone()
    return row[0] if row else None


def load_codes(conn, arg_code):
    if arg_code:
        if "." in arg_code:
            code, market = split_ts_code(arg_code)
            return {arg_code: {"raw_code": code, "market": market, "name": ""}}
        if len(arg_code) == 5 and arg_code.startswith("0"):
            market = "HK"
        elif arg_code.startswith(("0", "3")):
            market = "SZ"
        elif arg_code.startswith(("4", "8")):
            market = "BJ"
        else:
            market = "SH"
        return {to_ts_code(arg_code, market): {"raw_code": arg_code, "market": market, "name": ""}}

    equity_universe = load_active_equity_universe(conn, include_seed=True)
    result = {}
    for ts_code, meta in equity_universe.items():
        code, market = split_ts_code(ts_code)
        if market in {"SZ", "SH", "HK"}:
            result[ts_code] = {"raw_code": code, "market": market, "name": meta["name"]}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", help="Specific stock code, raw code or ts_code")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    codes = load_codes(conn, args.code)
    total = 0
    processed = 0
    processed_trade_dates = set()

    for ts_code, meta in codes.items():
        trade_date = latest_trade_date(conn, ts_code)
        if not trade_date:
            print(f"  {meta['raw_code']} {meta['name']}: no market data, skipped")
            continue

        try:
            factors = []
            if meta["market"] in {"SZ", "SH"}:
                spot_info = fetch_snapshot_a(meta["raw_code"])
                abstract_info = fetch_financial_abstract_a(meta["raw_code"])
                factors.extend(build_spot_factors_a(spot_info))
                factors.extend(build_financial_factors_a(abstract_info))
            elif meta["market"] == "HK":
                hk_info = fetch_financial_indicator_hk(meta["raw_code"])
                factors.extend(build_financial_factors_hk(hk_info))

            unique_factors = {}
            for fname, fval in factors:
                unique_factors[fname] = fval

            for fname, fval in unique_factors.items():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO factor_daily
                    (ts_code, trade_date, factor_name, factor_value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ts_code, trade_date, fname, fval),
                )
            processed += 1
            total += len(unique_factors)
            processed_trade_dates.add(trade_date)
            print(f"  {ts_code} {meta['name']}: {len(unique_factors)} factors")
            time.sleep(0.5)
        except Exception as e:
            print(f"  {ts_code} {meta['name']}: ERROR - {e}")
            time.sleep(1)

    register_snapshot(
        conn,
        entity_type="fundamental_factor_snapshot",
        entity_id=batch_entity_id(args.code),
        status="computed" if total else "empty",
        source="fundamental.py",
        relationships={"code_filter": args.code},
        payload={
            "requested_code": args.code,
            "processed_codes": processed,
            "factor_count": total,
            "latest_trade_dates": sorted(processed_trade_dates),
        },
    )
    conn.commit()
    conn.close()
    log_run(
        "fundamental.py",
        "success",
        "fundamental factors computed",
        {"processed": processed, "factor_count": total},
    )
    print(f"Computed {total} fundamental factors")


if __name__ == "__main__":
    main()
