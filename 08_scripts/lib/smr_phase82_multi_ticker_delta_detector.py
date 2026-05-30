def detect_multi_delta(baselines):
    rows=[];sc={"strengthened":0,"weakened":0,"unchanged":0,"baseline_missing":0}
    for b in baselines["phase82_multi_ticker_baseline"]["rows"]:
        if not b["baseline_available"]:ds="baseline_missing";rs="no_baseline";sc[ds]+=1;rows.append({"ticker":b["ticker"],"metric_name":b["metric_name"],"delta_status":ds,"delta_pct":0,"reason":rs})
        else:
            dp=round((b["latest_value"]-b["baseline_value"])/b["baseline_value"]*100,2)
            if b["metric_name"]=="revenue":ds="strengthened" if dp>=20 else("weakened" if dp<=-10 else"unchanged");rs=f"delta_{dp}pct"
            else:ds="unchanged";rs="delta_within_threshold"
            sc[ds]+=1;rows.append({"ticker":b["ticker"],"metric_name":b["metric_name"],"delta_status":ds,"delta_pct":dp,"reason":rs})
    return {"phase82_multi_ticker_delta":{"signals_checked":len(baselines["phase82_multi_ticker_baseline"]["rows"]),"strengthened":sc["strengthened"],"weakened":sc["weakened"],"unchanged":sc["unchanged"],"baseline_missing":sc["baseline_missing"],"rows":rows,"mock_used":False,"fixture_used":False}}
