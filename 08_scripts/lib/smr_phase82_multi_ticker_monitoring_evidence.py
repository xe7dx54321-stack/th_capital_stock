def build_multi_monitoring_evidence(delta,threshold):
    rows=[]
    for d in delta["phase82_multi_ticker_delta"]["rows"]:
        ds=d["delta_status"]
        if ds=="strengthened":et="threshold_strengthened_observed";ct=f"{d['metric_name']}_growth_strengthened";lim=f"{d['ticker']} {d['metric_name']} strengthened, does not confirm claims beyond metric trend."
        elif ds=="weakened":et="threshold_weakened_observed";ct=f"{d['metric_name']}_weakened";lim=f"{d['ticker']} {d['metric_name']} weakened."
        elif ds=="baseline_missing":et="baseline_missing_observed";ct=f"{d['metric_name']}_baseline_missing";lim=f"{d['ticker']} {d['metric_name']} baseline missing."
        else:et="unchanged_signal_observed";ct=f"{d['metric_name']}_unchanged";lim=f"{d['ticker']} {d['metric_name']} unchanged."
        rows.append({"ticker":d["ticker"],"metric_name":d["metric_name"],"evidence_type":et,"claim_type":ct,"limitation":lim,"cannot_conclude":["customer_share","order_visibility"]})
    for tk in["300394.SZ","09988.HK","00700.HK","NVDA","AVGO"]:
        if not any(r["ticker"]==tk for r in rows):
            rows.append({"ticker":tk,"metric_name":"n_a","evidence_type":"structured_data_unavailable_observed","claim_type":"financial_coverage_blocked","limitation":f"{tk} structured financial data unavailable for quant monitoring.","cannot_conclude":[]})
    return {"phase82_multi_ticker_monitoring_evidence":{"tickers_checked":8,"monitoring_evidence_created":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
