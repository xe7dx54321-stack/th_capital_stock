def run_hk_valuation_hardening():
    results = []
    for t, yf_sym, proxy_sym in [("09988.HK", "9988.HK", "BABA"), ("00700.HK", "0700.HK", "TCEHY")]:
        avail = []; miss = ["ev_revenue", "ev_ebitda"]; va = False; src = ""; attempted = []; errors = []; proxy_diag = None
        # Source 1: yfinance with correct HK format
        attempted.append("yfinance_" + yf_sym)
        try:
            import yfinance as yf
            info = yf.Ticker(yf_sym).info or {}
            if info.get("marketCap"): avail.append("market_cap")
            if info.get("trailingPE"): avail.append("pe_ttm")
            if info.get("priceToSalesTrailing12Months"): avail.append("ps_ttm")
            if info.get("priceToBook"): avail.append("pb")
            if avail: va = True; src = "yfinance_" + yf_sym
        except Exception as e:
            errors.append({"source": "yfinance_" + yf_sym, "error": str(e)[:200]})
        # Source 2: ADR proxy diagnostic
        if not va:
            attempted.append("yfinance_" + proxy_sym + "_ADR_proxy")
            try:
                import yfinance as yf
                info = yf.Ticker(proxy_sym).info or {}
                proxy_mc = info.get("marketCap")
                proxy_pe = info.get("trailingPE")
                proxy_ps = info.get("priceToSalesTrailing12Months")
                proxy_pb = info.get("priceToBook")
                proxy_diag = {"proxy_ticker": proxy_sym, "market_cap": proxy_mc, "pe_ttm": proxy_pe, "ps_ttm": proxy_ps, "pb": proxy_pb, "usage": "diagnostic_validation_only_not_final_metrics", "note": "ADR proxy confirms valuation metrics exist for related entity but does not replace direct HK listing data"}
            except Exception as e:
                errors.append({"source": "yfinance_" + proxy_sym + "_ADR_proxy", "error": str(e)[:200]})
        # Source 3: Derived valuation (attempt regardless)
        attempted.append("derived_valuation")
        derived = None
        try:
            from smr_phase83_hk_financial_adapter import run_hk_financial_adapter
            hk_data = run_hk_financial_adapter()
            for row in hk_data.get("phase83_hk_financial_adapter", {}).get("rows", []):
                if row["ticker"] == t and row.get("structured_data_available"):
                    metrics = row.get("metrics_available", [])
                    if "market_cap" in avail:
                        mc = None
                        try:
                            import yfinance as yf
                            mc = yf.Ticker(yf_sym).info.get("marketCap")
                        except: pass
                        if mc and "revenue" in metrics:
                            derived = {"ps_derived": "market_cap / revenue from phase83 financial data (derived=true)", "source": "cross_reference"}
                        if mc and "net_profit" in metrics:
                            if derived is None: derived = {}
                            derived["pe_derived"] = "market_cap / net_profit from phase83 financial data (derived=true)"
        except Exception as e:
            errors.append({"source": "derived_valuation", "error": str(e)[:200]})
        if not va:
            miss = sorted(set(miss + ["market_cap", "pe_ttm", "ps_ttm", "pb"]))
        final_status = "valuation_available" if va else ("derived_valuation_available" if derived else "final_unavailable_with_exhausted_sources")
        results.append({"ticker": t, "market": "HK", "status": final_status, "blocker": "" if va else ("all_hk_sources_exhausted" if not derived else "partial_derived_only"), "valuation_available": va, "derived_available": derived is not None, "metrics_available": sorted(set(avail)), "metrics_missing": sorted(set(miss)), "sources_attempted": attempted, "source_success": src if va else ("derived" if derived else "none"), "proxy_diagnostic": proxy_diag, "derived_metrics": derived, "source_errors": errors, "data_source": "real" if va else ("derived" if derived else "exhausted")})
    va_count = sum(1 for r in results if r["valuation_available"])
    dv_count = sum(1 for r in results if r.get("derived_available") and not r["valuation_available"])
    return {"phase85b_hk_valuation_hardening": {"tickers_checked": len(results), "valuation_available": va_count, "derived_available": dv_count, "fully_blocked": len(results) - va_count - dv_count, "rows": results, "mock_used": False, "fixture_used": False}}
