from smr_phase86_config import get_target_tickers, get_known_blocked, get_ticker_format, get_indices

def fetch_price_data(ticker, yf_sym):
    """Fetch price data from yfinance. Returns dict with price, change, history."""
    result = {"ticker": ticker, "yfinance_symbol": yf_sym, "price_available": False, "current_price": None, "prev_close": None, "change_pct": None, "change_5d_pct": None, "change_1mo_pct": None, "change_3mo_pct": None, "change_6mo_pct": None, "price_source": "", "price_errors": []}
    try:
        import yfinance as yf
        t = yf.Ticker(yf_sym)
        info = t.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
        chg = info.get("regularMarketChangePercent")
        if price:
            result["current_price"] = float(price)
            result["price_available"] = True
            result["price_source"] = "yfinance_info"
        if prev and price:
            result["prev_close"] = float(prev)
        if chg is not None:
            result["change_pct"] = float(chg)
        # History for multi-period
        periods = [("5d", "5d"), ("1mo", "1mo"), ("3mo", "3mo"), ("6mo", "6mo")]
        for label, p in periods:
            try:
                hist = t.history(period=p)
                if len(hist) > 1:
                    start_c = float(hist["Close"].iloc[0]); end_c = float(hist["Close"].iloc[-1])
                    if start_c > 0:
                        result[f"change_{label}_pct"] = round((end_c - start_c) / start_c * 100, 2)
            except: pass
    except Exception as e:
        result["price_errors"].append({"source": "yfinance", "error": str(e)[:200]})
    # Fallback: akshare for CN stocks
    if not result["price_available"] and (ticker.endswith(".SZ") or ticker.endswith(".SH")):
        try:
            import akshare as ak
            code = ticker.split(".")[0]
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code] if df is not None and "代码" in df.columns else None
            if row is not None and len(row) > 0:
                r = row.iloc[0]
                result["current_price"] = float(r.get("最新价", 0))
                result["change_pct"] = float(r.get("涨跌幅", 0))
                result["price_available"] = True
                result["price_source"] = "akshare_stock_zh_a_spot_em"
        except Exception as e:
            result["price_errors"].append({"source": "akshare_spot", "error": str(e)[:200]})
    return result

def run_pricing_adapter():
    results = []
    blocked = get_known_blocked()
    for t in get_target_tickers():
        yf_sym = get_ticker_format(t)
        if t in blocked:
            results.append({"ticker": t, "market": "CN_A", "pricing_status": "known_blocked", "pricing_available": False, "current_price": None, "change_pct": None, "price_source": "blocked", "blocker": "cninfo_org_id_missing", "price_errors": []})
            continue
        mkt = "CN_A"
        if t.endswith(".HK"): mkt = "HK"
        elif not (t.endswith(".SZ") or t.endswith(".SH")): mkt = "US"
        data = fetch_price_data(t, yf_sym)
        final_status = "pricing_available" if data["price_available"] else "pricing_unavailable_with_exhausted_sources"
        results.append({"ticker": t, "market": mkt, "pricing_status": final_status, "pricing_available": data["price_available"], "current_price": data["current_price"], "change_pct": data["change_pct"], "change_5d_pct": data.get("change_5d_pct"), "change_1mo_pct": data.get("change_1mo_pct"), "change_3mo_pct": data.get("change_3mo_pct"), "change_6mo_pct": data.get("change_6mo_pct"), "price_source": data["price_source"], "blocker": "" if data["price_available"] else "all_pricing_sources_exhausted", "price_errors": data["price_errors"]})
    avail = sum(1 for r in results if r["pricing_available"])
    unavail = len(results) - avail
    return {"phase86_pricing_adapter": {"tickers_checked": len(results), "pricing_available": avail, "pricing_unavailable": unavail, "rows": results, "mock_used": False, "fixture_used": False}}
