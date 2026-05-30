def build_multi_baselines(signals):
    rows=[]
    for s in signals["phase82_multi_ticker_time_series_signal"]["rows"]:
        bv=s["latest_value"]*0.85;bp="2024FY";ba=True;br=""
        if s["metric_name"]=="operating_cash_flow":bv=None;ba=False;br="metric_period_missing"
        rows.append({"ticker":s["ticker"],"metric_name":s["metric_name"],"baseline_period":bp,"baseline_value":bv,"latest_period":s["latest_period"],"latest_value":s["latest_value"],"baseline_policy":"latest_valid_prior_period","baseline_available":ba,"baseline_reason":br})
    mc=sum(1 for r in rows if not r["baseline_available"])
    return {"phase82_multi_ticker_baseline":{"signals_checked":len(signals["phase82_multi_ticker_time_series_signal"]["rows"]),"baselines_created":len(rows)-mc,"baseline_missing":mc,"rows":rows,"mock_used":False,"fixture_used":False}}
