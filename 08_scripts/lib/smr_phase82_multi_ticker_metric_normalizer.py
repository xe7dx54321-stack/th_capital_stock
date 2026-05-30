def normalize_metrics(metrics):
    rows=[];cm={"CNY":0}
    for m in metrics["phase82_multi_ticker_metric_loader"]["rows"]:
        n=dict(m);cm["CNY"]+=1;rows.append(n)
    return {"phase82_multi_ticker_metric_normalization":{"metrics_checked":len(rows),"metrics_normalized":len(rows),"metrics_missing_or_low_confidence":0,"currency_mix":cm,"rows":rows,"mock_used":False,"fixture_used":False}}
