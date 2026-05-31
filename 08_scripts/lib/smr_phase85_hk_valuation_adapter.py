def run_hk_valuation_adapter():
    results=[]
    for t in["09988.HK","00700.HK"]:
        metrics_avail=[];metrics_miss=["ev_revenue","ev_ebitda"];va=False;source=""
        try:
            import yfinance as yf;tk=yf.Ticker(t);info=tk.info or {}
            if info.get("marketCap"):metrics_avail.append("market_cap")
            if info.get("trailingPE"):metrics_avail.append("pe_ttm")
            if info.get("priceToSalesTrailing12Months"):metrics_avail.append("ps_ttm")
            if info.get("priceToBook"):metrics_avail.append("pb")
            if metrics_avail:va=True;source="yfinance_info"
            else:metrics_miss+=["market_cap","pe_ttm","ps_ttm","pb"]
        except Exception as e:
            metrics_miss+=["market_cap","pe_ttm","ps_ttm","pb"]
        if not va:metrics_miss=sorted(set(metrics_miss+["market_cap","pe_ttm","ps_ttm","pb"]));source=""
        results.append({"ticker":t,"market":"HK","status":"available" if va else "unavailable","blocker":"" if va else "valuation_metrics_unavailable_yfinance_404_or_no_fields","valuation_available":va,"metrics_available":sorted(set(metrics_avail)) if va else [],"metrics_missing":sorted(set(metrics_miss)),"source_attempted":["yfinance_info"],"source_success":source if va else "none","data_source":"real" if va else "none"})
    va_count=sum(1 for r in results if r["valuation_available"]);pa=sum(1 for r in results if r["valuation_available"] and r["metrics_missing"])
    return {"phase85_hk_valuation_adapter":{"tickers_checked":len(results),"valuation_available":va_count,"partial":pa,"blocked":0,"rows":results,"mock_used":False,"fixture_used":False}}
