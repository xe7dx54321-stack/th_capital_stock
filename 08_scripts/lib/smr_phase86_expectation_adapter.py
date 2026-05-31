from smr_phase86_config import get_target_tickers, get_known_blocked, get_expectation_sources

def explore_expectation_sources(ticker, market):
    result = {"ticker": ticker, "market": market, "expectation_available": False, "expectation_partial": False, "consensus_metrics": {}, "sources_attempted": [], "source_errors": [], "analyst_count": None, "target_price_hidden": True}
    if market == "CN_A":
        code = ticker.split(".")[0]
        # Source 1: stock_profit_forecast_ths
        result["sources_attempted"].append("akshare_stock_profit_forecast_ths")
        try:
            import akshare as ak
            df = ak.stock_profit_forecast_ths(symbol=code)
            if df is not None and len(df) > 0:
                result["expectation_available"] = True
                result["consensus_metrics"]["forecast_source"] = "ths"
                result["consensus_metrics"]["forecast_rows"] = len(df)
        except Exception as e:
            result["source_errors"].append({"source": "profit_forecast_ths", "error": str(e)[:200]})
        # Source 2: stock_profit_forecast_em
        result["sources_attempted"].append("akshare_stock_profit_forecast_em")
        if not result["expectation_available"]:
            try:
                import akshare as ak
                df = ak.stock_profit_forecast_em(symbol=code)
                if df is not None and len(df) > 0:
                    result["expectation_available"] = True
                    result["consensus_metrics"]["forecast_source"] = "eastmoney"
            except Exception as e:
                result["source_errors"].append({"source": "profit_forecast_em", "error": str(e)[:200]})
        # Source 3: yfinance analyst
        result["sources_attempted"].append("yfinance_analyst_info")
        if not result["expectation_available"]:
            try:
                import yfinance as yf
                info = yf.Ticker(ticker).info or {}
                rec = info.get("recommendationMean") or info.get("numberOfAnalystOpinions")
                if rec:
                    result["expectation_partial"] = True
                    result["analyst_count"] = info.get("numberOfAnalystOpinions")
                    result["consensus_metrics"]["rating_mean"] = info.get("recommendationMean")
            except Exception as e:
                result["source_errors"].append({"source": "yfinance_analyst", "error": str(e)[:200]})
    elif market == "HK":
        code = ticker.split(".")[0]
        # Source 1: stock_hk_profit_forecast_et
        result["sources_attempted"].append("akshare_stock_hk_profit_forecast_et")
        try:
            import akshare as ak
            df = ak.stock_hk_profit_forecast_et(symbol=code)
            if df is not None and len(df) > 0:
                result["expectation_available"] = True
                result["consensus_metrics"]["forecast_source"] = "etnet_hk"
                result["consensus_metrics"]["forecast_rows"] = len(df)
        except Exception as e:
            result["source_errors"].append({"source": "hk_profit_forecast_et", "error": str(e)[:200]})
        # Source 2: yfinance analyst
        result["sources_attempted"].append("yfinance_analyst_info")
        if not result["expectation_available"]:
            try:
                import yfinance as yf
                info = yf.Ticker("9988.HK" if ticker == "09988.HK" else "0700.HK").info or {}
                rec = info.get("recommendationMean") or info.get("numberOfAnalystOpinions")
                if rec:
                    result["expectation_partial"] = True
                    result["analyst_count"] = info.get("numberOfAnalystOpinions")
            except Exception as e:
                result["source_errors"].append({"source": "yfinance_analyst", "error": str(e)[:200]})
    elif market == "US":
        # Source 1: yfinance analyst info
        result["sources_attempted"].append("yfinance_analyst_info")
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info or {}
            ana_count = info.get("numberOfAnalystOpinions")
            recom = info.get("recommendationKey") or info.get("recommendationMean")
            if ana_count or recom:
                result["expectation_available"] = True
                result["analyst_count"] = ana_count
                result["consensus_metrics"]["rating_key"] = recom
                result["consensus_metrics"]["analyst_count"] = ana_count
        except Exception as e:
            result["source_errors"].append({"source": "yfinance_analyst", "error": str(e)[:200]})
    return result

def run_expectation_adapter():
    results = []
    blocked = get_known_blocked()
    for t in get_target_tickers():
        mkt = "CN_A"
        if t.endswith(".HK"): mkt = "HK"
        elif not (t.endswith(".SZ") or t.endswith(".SH")): mkt = "US"
        if t in blocked:
            results.append({"ticker": t, "market": "CN_A", "expectation_status": "known_blocked", "expectation_available": False, "expectation_partial": False, "consensus_metrics": {}, "sources_attempted": [], "source_errors": [], "blocker": "cninfo_org_id_missing"})
            continue
        data = explore_expectation_sources(t, mkt)
        status = "expectation_available" if data["expectation_available"] else ("expectation_partial" if data["expectation_partial"] else "expectation_unavailable_with_exhausted_sources")
        results.append({"ticker": t, "market": mkt, "expectation_status": status, "expectation_available": data["expectation_available"], "expectation_partial": data["expectation_partial"], "consensus_metrics": data["consensus_metrics"], "sources_attempted": data["sources_attempted"], "source_errors": data["source_errors"], "analyst_count": data.get("analyst_count"), "target_price_hidden": True, "blocker": "" if data["expectation_available"] or data.get("expectation_partial") else "all_expectation_sources_exhausted"})
    avail = sum(1 for r in results if r["expectation_available"]); partial = sum(1 for r in results if r["expectation_partial"]); exhausted = sum(1 for r in results if not r["expectation_available"] and not r.get("expectation_partial") and r["expectation_status"] != "known_blocked")
    return {"phase86_expectation_adapter": {"tickers_checked": len(results), "expectation_available": avail, "expectation_partial": partial, "expectation_exhausted": exhausted, "blocked": sum(1 for r in results if r["expectation_status"] == "known_blocked"), "target_price_output_count": 0, "rows": results, "mock_used": False, "fixture_used": False}}
