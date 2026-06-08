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

    def get_market_data(self, tickers, date_str="20250606", indicators=None):
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

    def get_financial_data(self, tickers, report_date="20251231", indicators=None):
        if indicators is None:
            indicators = list(WORKING_FINANCIAL.keys())
        indipara = [{"indicator": "ths_stock_short_name_stock", "indiparams": []}]
        for key in indicators:
            cfg = WORKING_FINANCIAL[key]
            params = [report_date if p == "DATE_PLACEHOLDER" else p for p in cfg["params"]]
            indipara.append({"indicator": cfg["indicator"], "indiparams": params})

        codes = ",".join(tickers) if isinstance(tickers, list) else tickers
        return self.client.call("basic_data_service", {"codes": codes, "indipara": indipara})

    def get_full_snapshot(self, tickers, market_date="20250606", report_date="20251231"):
        market = self.get_market_data(tickers, market_date)
        financial = self.get_financial_data(tickers, report_date)
        return {"market": market, "financial": financial, "timestamp": datetime.now().isoformat()}


def run_smoke():
    adapter = IFindAdapter()
    print("Health: {}".format(json.dumps(adapter.health_check(), ensure_ascii=False)))

    tickers_all = ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"]

    print("\n=== Market Data ===")
    result = adapter.get_market_data(tickers_all, "20250606")
    for t in result.get("tables", []):
        tbl = t["table"]
        print("  {} {}: close={} pe={} pb={}".format(
            t["thscode"],
            tbl.get("ths_stock_short_name_stock", ["?"])[0],
            tbl.get("ths_close_price_stock", [None])[0],
            tbl.get("ths_pe_ttm_stock", [None])[0],
            tbl.get("ths_pb_mrq_stock", [None])[0],
        ))

    print("\n=== Financial Data (2025年报) ===")
    fin = adapter.get_financial_data(["300308.SZ", "688041.SH", "002230.SZ"], "20251231")
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
