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


def _fetch_snapshot_a_em(code):
    """
    用东方财富 stock/get 接口获取 A 股个股实时行情（内部辅助函数）。

    【功能】
    通过 HTTP 请求东方财富 push2 服务器，获取单只股票的实时行情数据。
    东方财富接口稳定性高于雪球，作为 fetch_snapshot_a 的主力数据源。

    【参数】
    code (str): 6 位股票代码，例如 "000001"（平安银行）、"600519"（贵州茅台）。

    【返回值】
    dict: 行情数据字典，key 为中文指标名（与雪球接口返回格式一致），
          value 为指标值。主要包含：
          - 现价、总股本、流通股
          - 市盈率(TTM)、市盈率(动)、市盈率(静)
          - 市净率
          - 每股收益（由 现价/市盈率(TTM) 反推）
          - 每股净资产（由 现价/市净率 反推）

    【异常处理】
    网络请求失败、HTTP 状态码非 200、返回数据为空时抛出 Exception，
    由上层 fetch_snapshot_a 捕获并回退到雪球接口。

    【小白讲解】
    东方财富的接口就像一个网址，我们带上股票代码去访问它，
    它会返回这只股票的实时价格、市盈率、市净率等数据。
    fltt=2 参数的意思是"把数字都转成正常格式"（比如价格直接是 10.52，而不是 1052）。
    """
    import requests
    import time

    # 使用模块级 Session 复用 TCP 连接，减少连接建立开销，降低被限流概率
    global _EM_SESSION
    if "_EM_SESSION" not in globals() or _EM_SESSION is None:
        _EM_SESSION = requests.Session()
        _EM_SESSION.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://quote.eastmoney.com/",
        })

    # 东方财富 secid 格式：市场代码.股票代码
    # 1 = 沪市（代码以 6 开头），0 = 深市（代码以 0/3 开头）或北交所（代码以 4/8 开头）
    if code.startswith("6"):
        secid = f"1.{code}"
    else:
        secid = f"0.{code}"

    url = "http://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": secid,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",  # fltt=2 表示返回扁平化数值（价格/比率已经是正常值，不需要除以 100）
        "fields": "f43,f57,f58,f84,f85,f116,f117,f162,f163,f164,f167",
    }

    # 带重试的请求（最多 3 次，应对东方财富的偶发限流）
    last_err = None
    data = None
    for attempt in range(3):
        try:
            r = _EM_SESSION.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json().get("data")
            if data:
                break
            else:
                raise ValueError(f"东方财富返回空数据: secid={secid}")
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))  # 第1次重试等1.5秒，第2次等3秒
    if not data:
        raise last_err if last_err else ValueError(f"东方财富返回空数据: secid={secid}")

    # 字段映射（东方财富字段代码 -> 雪球中文字段名）
    # fltt=2 时返回值已经是正常数值，不需要额外除以 100
    price = data.get("f43")         # 最新价
    total_shares = data.get("f84")  # 总股本
    float_shares = data.get("f85")  # 流通股本
    pe_dynamic = data.get("f162")   # 市盈率(动态)
    pe_static = data.get("f163")    # 市盈率(静态)
    pe_ttm = data.get("f164")       # 市盈率(TTM)
    pb = data.get("f167")           # 市净率

    info = {
        "现价": price,
        "总股本": total_shares,
        "流通股": float_shares,
        "市盈率(TTM)": pe_ttm,
        "市盈率(动)": pe_dynamic,
        "市盈率(静)": pe_static,
        "市净率": pb,
    }

    # 每股收益和每股净资产通过反推得到
    # 公式：每股收益 = 现价 / 市盈率(TTM)，每股净资产 = 现价 / 市净率
    # 这样可以避免依赖额外的财务数据接口
    try:
        if price and pe_ttm and float(pe_ttm) != 0:
            info["每股收益"] = float(price) / float(pe_ttm)
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    try:
        if price and pb and float(pb) != 0:
            info["每股净资产"] = float(price) / float(pb)
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    return info


def fetch_snapshot_a(code):
    """
    获取 A 股个股的实时行情快照（东方财富为主，雪球兜底）。

    【功能】
    先尝试用东方财富 stock/get 接口获取个股实时行情，
    如果东方财富接口失败，则回退到雪球接口（ak.stock_individual_spot_xq）。
    由于雪球反爬加强，东方财富接口作为主力数据源。

    【参数】
    code (str): 6 位股票代码，例如 "000001"（平安银行）、"600519"（贵州茅台）。

    【返回值】
    dict: 个股行情数据字典，key 为中文指标名（与雪球接口返回格式一致），
          value 为指标值。主要包含：
          - 现价、总股本、流通股
          - 市盈率(TTM)、市盈率(动)、市盈率(静)
          - 市净率
          - 每股收益、每股净资产
          如果两个接口都失败，返回空字典 {}。

    【异常处理】
    - 东方财富接口失败时，记录警告日志，并回退到雪球接口。
    - 雪球接口也失败时，记录错误日志，返回空字典。
    - 不会向上抛出异常，保证主流程不中断。

    【小白讲解】
    这个函数就像一个"双保险"的数据获取器：
    先问东方财富要数据，如果东方财富不给（比如网络断了），
    就去问雪球要。两个都给不了，就返回空字典，让程序继续跑别的股票。
    """
    import akshare as ak
    import logging

    logger = logging.getLogger(__name__)

    # ---- 第 1 步：尝试东方财富 stock/get 接口 ----
    try:
        return _fetch_snapshot_a_em(code)
    except Exception as e:
        msg = f"东方财富接口失败 code={code}: {type(e).__name__}: {e}"
        logger.warning(msg)
        print(f"  [warn] {msg}，回退到雪球接口")

    # ---- 第 2 步：回退到雪球接口 ----
    try:
        df = ak.stock_individual_spot_xq(symbol=to_xq_symbol(code))
        return dict(zip(df["item"], df["value"]))
    except Exception as e:
        msg = f"雪球接口也失败 code={code}: {type(e).__name__}: {e}"
        logger.error(msg)
        print(f"  [error] {msg}")
        return {}


def fetch_financial_abstract_a(code):
    import akshare as ak

    df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
    if df.empty:
        return {}
    latest = df.iloc[-1].to_dict()
    return latest


def fetch_financial_indicator_hk(code):
    """港股财务指标获取（东方财富接口）。返回原始字段 dict。"""
    import akshare as ak

    df = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
    if df.empty:
        return {}
    latest = df.iloc[0].to_dict()
    return latest


def fetch_financial_us(code):
    """美股财务指标获取（东方财富接口）。返回原始字段 dict。

    【小白讲解】
    这个函数用 akshare 去东方财富抓美股的财务报告。
    接口名 stock_financial_us_analysis_indicator_em 虽然长，但很管用。
    返回的字段名都是大写英文（如 OPERATE_INCOME 就是营业收入）。
    失败时返回空字典，不会让程序崩。
    """
    import akshare as ak

    try:
        df = ak.stock_financial_us_analysis_indicator_em(symbol=code)
        if df.empty:
            return {}
        latest = df.iloc[0].to_dict()
        return latest
    except Exception as e:
        print(f"    [warn] fetch_financial_us({code}) failed: {e}")
        return {}


def _compute_valuation_from_price(conn, ts_code, market, financial_info):
    """用 daily_bar/us_daily_bar 的最新收盘价 + 财务数据反推 PE/PB/市值。

    【小白讲解】
    东方财富的实时行情接口有时不稳定（连不上）。
    但我们数据库里已经有历史价格（close）和财务数据（EPS、净利润）。
    估值公式其实很简单：
        PE = 股价 / 每股收益（EPS）
        PB = 股价 / 每股净资产（BPS）
        总股本 = 净利润 / EPS
        市值 = 股价 * 总股本
    这样我们不需要依赖实时行情接口也能算出估值。

    参数：
        conn: 数据库连接
        ts_code: 标的代码（如 00981.HK 或 NVDA）
        market: "HK" / "US" / "SZ" / "SH"
        financial_info: fetch_financial_xxx 返回的原始数据

    返回：
        [(factor_name, factor_value), ...] 列表，可直接 extend 到 factors
    """
    # 1. 取最新收盘价
    if market == "US":
        table = "us_daily_bar"
        code_field = "symbol"
    else:
        table = "daily_bar"
        code_field = "ts_code"

    price_row = conn.execute(
        f"SELECT close FROM {table} WHERE {code_field}=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    ).fetchone()
    if not price_row:
        return []
    close = safe_float(price_row[0])
    if close is None or close <= 0:
        return []

    # 2. 从财务数据中拿 EPS 和 BPS
    # 港股字段: EPS_TTM, BASIC_EPS, BPS, HOLDER_PROFIT
    # 美股字段: BASIC_EPS, DILUTED_EPS, OPERATE_INCOME, PARENT_HOLDER_NETPROFIT
    eps = safe_float(financial_info.get("EPS_TTM")) or safe_float(financial_info.get("BASIC_EPS"))
    bps = safe_float(financial_info.get("BPS"))
    net_profit = safe_float(financial_info.get("HOLDER_PROFIT")) or safe_float(
        financial_info.get("PARENT_HOLDER_NETPROFIT")
    )

    factors = []

    # 3. 计算 PE_TTM
    if eps is not None and eps > 0:
        pe_ttm = round(close / eps, 4)
        factors.append(("pe_ttm", pe_ttm))

    # 4. 计算 PB
    if bps is not None and bps > 0:
        pb = round(close / bps, 4)
        factors.append(("pb", pb))

    # 5. 估算市值（close * 总股本），总股本 = 净利润 / EPS
    # 注意：财务数据的净利润单位是港元或美元，计算的市值单位一致
    if close is not None and eps is not None and eps > 0 and net_profit is not None and net_profit > 0:
        shares_est = net_profit / eps  # 估算总股本
        market_cap = close * shares_est
        # 统一转成"亿元"单位方便比较（H股和美股的货币不同，
        # 但我们只用于产业位置排序，不做跨市场比较，所以可以接受）
        # 简化处理：直接存原始值，让评分器自己判断大小
        factors.append(("market_cap", round(market_cap, 2)))
        factors.append(("float_market_cap", round(market_cap * 0.7, 2)))  # 估算流通市值（70%）

    # 6. 如果有 EPS，存一份作为价值评分器的参考
    if eps is not None:
        factors.append(("basic_eps_reported", round(eps, 4)))

    # 7. 如果有 BPS，存一份
    if bps is not None:
        factors.append(("bps_reported", round(bps, 4)))

    return factors


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
    """港股财务因子映射：东方财富英文字段 -> SMR 标准因子名。"""
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


def build_financial_factors_us(info):
    """美股财务因子映射：东方财富英文字段 -> SMR 标准因子名。

    【小白讲解】
    美股财务接口返回的字段名跟港股很像（都是大写英文），
    但有些字段名不同（比如美股净利润叫 PARENT_HOLDER_NETPROFIT，
    港股叫 HOLDER_PROFIT）。这里把它们映射到我们系统统一的因子名。
    """
    if not info:
        return []

    amount_mapping = {
        "revenue": "OPERATE_INCOME",
        "gross_profit": "GROSS_PROFIT",
        "holder_profit": "PARENT_HOLDER_NETPROFIT",
    }
    mapping = {
        "revenue_yoy": "OPERATE_INCOME_YOY",
        "net_profit_yoy": "PARENT_HOLDER_NETPROFIT_YOY",
        "gross_margin": "GROSS_PROFIT_RATIO",
        "net_margin": "NET_PROFIT_RATIO",
        "roe_reported": "ROE_AVG",
        "roa": "ROA",
        "current_ratio": "CURRENT_RATIO",
        "debt_asset_ratio": "DEBT_ASSET_RATIO",
        "equity_ratio": "EQUITY_RATIO",
        "basic_eps_reported": "BASIC_EPS",
        "eps_ttm": "BASIC_EPS",  # 美股没有独立 EPS_TTM 字段，用 BASIC_EPS 替代
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


def latest_trade_date(conn, ts_code, market=None):
    """获取标的的最新交易日（支持从 daily_bar 或 us_daily_bar 查）。

    参数：
        market: 如果给了，US 查 us_daily_bar，其他查 daily_bar；
                如果没给，根据 ts_code 后缀自动判断。
    """
    # 自动判断市场
    if market is None:
        if ts_code.endswith(".HK") or ts_code.endswith(".SZ") or ts_code.endswith(".SH") or ts_code.endswith(".BJ"):
            market = "AH"
        else:
            market = "US"

    if market == "US":
        table = "us_daily_bar"
        code_field = "symbol"
    else:
        table = "daily_bar"
        code_field = "ts_code"

    row = conn.execute(
        f"SELECT trade_date FROM {table} WHERE {code_field}=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    ).fetchone()
    return row[0] if row else None


def load_codes(conn, arg_code):
    """加载需要采集基本面因子的标的列表。

    【小白讲解】
    原来只处理 SZ/SH/HK，现在加上了美股（US）。
    美股代码没有后缀（直接是 NVDA、MRVL），
    我们用 split_ts_code 的返回值来判断市场。
    """
    if arg_code:
        # 命令行指定单只标的
        if "." in arg_code:
            # 有后缀的（如 00981.HK, 000001.SZ）
            try:
                code, market = split_ts_code(arg_code)
            except Exception:
                market = "SH"
                code = arg_code
            return {arg_code: {"raw_code": code, "market": market, "name": ""}}
        # 纯数字或英文代码（如 00981 或 NVDA）
        if arg_code[0].isalpha():
            market = "US"
            raw_code = arg_code
            return {raw_code: {"raw_code": raw_code, "market": market, "name": ""}}
        if len(arg_code) == 5:
            market = "HK"
        elif arg_code.startswith(("0", "3")):
            market = "SZ"
        elif arg_code.startswith(("4", "8")):
            market = "BJ"
        else:
            market = "SH"
        return {to_ts_code(arg_code, market): {"raw_code": arg_code, "market": market, "name": ""}}

    # 批量加载：从 equity_universe 读取，同时支持 A/H/US
    equity_universe = load_active_equity_universe(conn, include_seed=True)
    result = {}
    for ts_code, meta in equity_universe.items():
        try:
            code, market = split_ts_code(ts_code)
        except Exception:
            # split_ts_code 可能不认识美股代码（纯字母）
            if ts_code and not ts_code.endswith((".HK", ".SZ", ".SH", ".BJ")):
                market = "US"
                code = ts_code
            else:
                continue
        if market in {"SZ", "SH", "HK", "US"}:
            result[ts_code] = {"raw_code": code, "market": market, "name": meta.get("name", "")}
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
        trade_date = latest_trade_date(conn, ts_code, meta["market"])
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
                # H股：先拿财务指标，再用价格反推估值
                hk_info = fetch_financial_indicator_hk(meta["raw_code"])
                factors.extend(build_financial_factors_hk(hk_info))
                # 用 daily_bar 最新价格 + EPS/BPS 反推 PE/PB/市值
                derived = _compute_valuation_from_price(conn, ts_code, "HK", hk_info)
                factors.extend(derived)
            elif meta["market"] == "US":
                # 美股：拿财务指标，再用 us_daily_bar 价格反推估值
                us_info = fetch_financial_us(meta["raw_code"])
                factors.extend(build_financial_factors_us(us_info))
                # 用 us_daily_bar 最新价格反推 PE/PB/市值
                derived = _compute_valuation_from_price(conn, ts_code, "US", us_info)
                factors.extend(derived)

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
