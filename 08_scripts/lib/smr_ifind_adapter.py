"""iFinD adapter for th_capital_stock — production version with confirmed working indicators."""
import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from ifind_client import IFindClient, mask_token

CN_TICKERS = ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"]
HK_TICKERS = ["9988.HK", "0700.HK"]
US_TICKERS = ["NVDA.O", "AVGO.O"]  # NASDAQ: use .O suffix per iFinD API spec
ALL_IFIND_TICKERS = CN_TICKERS + HK_TICKERS + US_TICKERS

WORKING_MARKET = {
    "close_price": {"indicator": "ths_close_price_stock", "params": ["DATE_PLACEHOLDER", "100", "DATE_PLACEHOLDER"]},
    "pe_ttm": {"indicator": "ths_pe_ttm_stock", "params": ["DATE_PLACEHOLDER"]},
    "pb_mrq": {"indicator": "ths_pb_mrq_stock", "params": ["DATE_PLACEHOLDER"]},
    "turnover_ratio": {"indicator": "ths_turnover_ratio_stock", "params": ["DATE_PLACEHOLDER"]},
}

WORKING_FINANCIAL = {
    "revenue": {"indicator": "ths_revenue_stock", "params": ["DATE_PLACEHOLDER"]},
    "net_profit": {"indicator": "ths_np_atoopc_stock", "params": ["DATE_PLACEHOLDER"]},
    "roe": {"indicator": "ths_roe_stock", "params": ["DATE_PLACEHOLDER"]},
    "eps_basic": {"indicator": "ths_eps_basic_stock", "params": ["DATE_PLACEHOLDER"]},
}


def _get_latest_trade_date():
    """
    动态获取最近一个 A 股交易日（格式 YYYYMMDD）。

    功能说明（小白版）：
        这个函数会根据"现在"是几点几分，自动算出最近一个已经收盘的 A 股交易日。
        比如周三下午调用就返回今天，周日调用就返回上周五。
        它会复用项目里 smr_trade_calendar.py 已经写好的交易日逻辑，
        包括跳过周末和节假日。

    参数：
        无

    返回值：
        str: 8 位日期字符串，例如 "20240606"（仅作格式示例）

    异常处理：
        如果 smr_trade_calendar 模块加载失败或出错，
        会退回到"只跳过周末"的简单逻辑，保证函数不会崩。
    """
    try:
        from smr_trade_calendar import expected_trade_date
        trade_date = expected_trade_date(datetime.now(), "A")
        return trade_date.strftime("%Y%m%d")
    except Exception:
        # 兜底方案：日历模块不可用时，至少跳过周六周日
        from datetime import timedelta
        d = datetime.now().date()
        while d.weekday() >= 5:  # 5=周六, 6=周日
            d -= timedelta(days=1)
        return d.strftime("%Y%m%d")


def _get_latest_report_period():
    """
    根据当前月份推断最新可用的财报期（格式 YYYYMMDD）。

    功能说明（小白版）：
        A 股公司一年发四次财报，但披露有时间窗口，不能随时拿到最新一期。
        这个函数按当前月份返回"最近一份已经披露完的财报"对应的日期：
        - 1~4 月：上一年三季报（9 月 30 日），例如 2024 年 3 月调用返回 "20230930"
        - 5~8 月：上一年年报（12 月 31 日），例如 2025 年 6 月调用返回 "20241231"
        - 9~10 月：当年一季报（3 月 31 日），例如 2025 年 9 月调用返回 "20250331"
        - 11~12 月：当年中报（6 月 30 日），例如 2025 年 11 月调用返回 "20250630"

    参数：
        无

    返回值：
        str: 8 位日期字符串，例如 "20241231"
    """
    now = datetime.now()
    year = now.year
    month = now.month
    if 1 <= month <= 4:
        # 1-4 月：上年三季报已披露完，年报还没全部披露
        return "{}0930".format(year - 1)
    elif 5 <= month <= 8:
        # 5-8 月：上年年报披露完毕
        return "{}1231".format(year - 1)
    elif 9 <= month <= 10:
        # 9-10 月：当年一季报已披露完
        return "{}0331".format(year)
    else:
        # 11-12 月：当年中报已披露完
        return "{}0630".format(year)


class IFindAdapter:
    def __init__(self):
        tok = os.getenv("IFIND_REFRESH_TOKEN")
        if not tok:
            tok_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ifind_refresh_token.txt")
            if os.path.exists(tok_file):
                with open(tok_file, "r", encoding="utf-8") as f:
                    tok = f.read().strip()
        if not tok:
            raise RuntimeError("No IFIND_REFRESH_TOKEN. Set env or config/ifind_refresh_token.txt")
        self.client = IFindClient(refresh_token=tok, timeout=30)

    def health_check(self):
        try:
            token = self.client.get_access_token()
            return {"status": "connected", "token_masked": mask_token(token), "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def get_market_data(self, tickers, date_str=None, indicators=None):
        """
        获取股票的市场行情数据（收盘价、PE、PB、换手率等）。

        参数（小白版）：
            tickers (list[str] | str): 股票代码列表，比如 ["300308.SZ", "688041.SH"]；
                也可以直接传逗号分隔的字符串
            date_str (str | None): 查询日期，8 位字符串如 "20240606"（仅作格式示例）。
                传 None（默认）时会自动取最近一个 A 股交易日，省得自己算
            indicators (list[str] | None): 想要哪些指标，比如 ["close_price", "pe_ttm"]。
                传 None 时取全部默认指标

        返回值：
            dict: iFinD 接口返回的原始数据
        """
        if date_str is None:
            date_str = _get_latest_trade_date()
        if indicators is None:
            indicators = list(WORKING_MARKET.keys())
        indipara = []
        for key in indicators:
            cfg = WORKING_MARKET[key]
            params = [date_str if p == "DATE_PLACEHOLDER" else p for p in cfg["params"]]
            indipara.append({"indicator": cfg["indicator"], "indiparams": params})
        indipara.insert(0, {"indicator": "ths_stock_short_name_stock", "indiparams": []})

        codes = ",".join(tickers) if isinstance(tickers, list) else tickers
        return self.client.call("basic_data_service", {"codes": codes, "indipara": indipara})

    def get_financial_data(self, tickers, report_date=None, indicators=None):
        """
        获取股票的财务数据（营收、净利润、ROE、每股收益等）。

        参数（小白版）：
            tickers (list[str] | str): 股票代码列表，比如 ["300308.SZ"]；
                也可以直接传逗号分隔的字符串
            report_date (str | None): 财报期，8 位字符串如 "20241231"。
                传 None（默认）时会自动根据当前月份推断最新可用的财报期，
                避免拿到还没披露完的数据
            indicators (list[str] | None): 想要哪些财务指标。
                传 None 时取全部默认指标

        返回值：
            dict: iFinD 接口返回的原始数据
        """
        if report_date is None:
            report_date = _get_latest_report_period()
        if indicators is None:
            indicators = list(WORKING_FINANCIAL.keys())
        indipara = [{"indicator": "ths_stock_short_name_stock", "indiparams": []}]
        for key in indicators:
            cfg = WORKING_FINANCIAL[key]
            params = [report_date if p == "DATE_PLACEHOLDER" else p for p in cfg["params"]]
            indipara.append({"indicator": cfg["indicator"], "indiparams": params})

        codes = ",".join(tickers) if isinstance(tickers, list) else tickers
        return self.client.call("basic_data_service", {"codes": codes, "indipara": indipara})

    def get_full_snapshot(self, tickers, market_date=None, report_date=None):
        """
        一次性拿到行情 + 财务数据的完整快照。

        参数（小白版）：
            tickers (list[str] | str): 股票代码列表
            market_date (str | None): 行情日期，None 时自动取最近 A 股交易日
            report_date (str | None): 财报期，None 时自动取最新可用财报期

        返回值：
            dict: 包含 market（行情）、financial（财务）、timestamp（时间戳）三个字段
        """
        market = self.get_market_data(tickers, market_date)
        financial = self.get_financial_data(tickers, report_date)
        return {"market": market, "financial": financial, "timestamp": datetime.now().isoformat()}


def run_smoke():
    adapter = IFindAdapter()
    print("Health: {}".format(json.dumps(adapter.health_check(), ensure_ascii=False)))

    tickers_all = ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"]

    print("\n=== Market Data ===")
    result = adapter.get_market_data(tickers_all)
    for t in result.get("tables", []):
        tbl = t["table"]
        print("  {} {}: close={} pe={} pb={}".format(
            t["thscode"],
            tbl.get("ths_stock_short_name_stock", ["?"])[0],
            tbl.get("ths_close_price_stock", [None])[0],
            tbl.get("ths_pe_ttm_stock", [None])[0],
            tbl.get("ths_pb_mrq_stock", [None])[0],
        ))

    print("\n=== Financial Data ===")
    fin = adapter.get_financial_data(["300308.SZ", "688041.SH", "002230.SZ"])
    for t in fin.get("tables", []):
        tbl = t["table"]
        rev = tbl.get("ths_revenue_stock", [None])[0]
        np_ = tbl.get("ths_np_atoopc_stock", [None])[0]
        roe = tbl.get("ths_roe_stock", [None])[0]
        eps = tbl.get("ths_eps_basic_stock", [None])[0]
        print("  {} {}: rev={} np={} roe={}% eps={}".format(
            t["thscode"],
            tbl.get("ths_stock_short_name_stock", ["?"])[0],
            "{}B".format(round(rev/1e8, 1)) if rev else None,
            "{}M".format(round(np_/1e6, 1)) if np_ else None,
            roe, eps,
        ))

    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--market", action="store_true")
    p.add_argument("--financial", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.market:
        adapter = IFindAdapter()
        r = adapter.get_market_data(CN_TICKERS)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.financial:
        adapter = IFindAdapter()
        r = adapter.get_financial_data(CN_TICKERS)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        run_smoke()

# HK tickers use 4-digit format (9988.HK not 09988.HK) per iFinD API spec
