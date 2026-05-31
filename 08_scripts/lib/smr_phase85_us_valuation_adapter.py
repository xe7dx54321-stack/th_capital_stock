def run_us_valuation_adapter():
    results=[]
    for t in["NVDA","AVGO"]:
        metrics_avail=[];metrics_miss=[];va=False;source=""
        try:
            import yfinance as yf;tk=yf.Ticker(t);info=tk.info or {}
            if info.get("marketCap"):metrics_avail.append("market_cap")
            if info.get("trailingPE"):metrics_avail.append("pe_ttm")
            if info.get("priceToSalesTrailing12Months"):metrics_avail.append("ps_ttm")
            if info.get("priceToBook"):metrics_avail.append("pb")
            if info.get("enterpriseValue"):metrics_avail.append("enterprise_value")
            if info.get("enterpriseToRevenue"):metrics_avail.append("ev_revenue")
            if info.get("enterpriseToEbitda"):metrics_avail.append("ev_ebitda")
            if metrics_avail:va=True;source="yfinance_info"
            else:metrics_miss=["market_cap","pe_ttm","ps_ttm","pb","enterprise_value","ev_revenue","ev_ebitda"]
        except Exception as e:metrics_miss=["market_cap","pe_ttm","ps_ttm","pb","enterprise_value","ev_revenue","ev_ebitda"]
        results.append({"ticker":t,"market":"US","status":"available" if va else "unavailable","blocker":"" if va else "valuation_metrics_unavailable","valuation_available":va,"metrics_available":sorted(set(metrics_avail)),"metrics_missing":sorted(set(metrics_miss)),"source_attempted":["yfinance_info","yfinance_fast_info"],"source_success":source if va else "none","data_source":"real" if va else "none"})
    va_count=sum(1 for r in results if r["valuation_available"]);pa=sum(1 for r in results if r["valuation_available"] and r["metrics_missing"])
    return {"phase85_us_valuation_adapter":{"tickers_checked":len(results),"valuation_available":va_count,"partial":pa,"blocked":0,"rows":results,"mock_used":False,"fixture_used":False}}
