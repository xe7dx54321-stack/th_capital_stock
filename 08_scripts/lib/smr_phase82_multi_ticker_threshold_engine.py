def run_multi_threshold(delta):
    rows=[];sc={"triggered_strengthened":0,"triggered_weakened":0,"triggered_anomaly":0,"not_triggered":0}
    for d in delta["phase82_multi_ticker_delta"]["rows"]:
        ds=d["delta_status"];dp=d.get("delta_pct",0)
        if ds=="strengthened":rs="triggered_strengthened";sc[rs]+=1
        elif ds=="weakened":rs="triggered_weakened";sc[rs]+=1
        elif dp>35:rs="triggered_anomaly";sc[rs]+=1
        elif ds=="baseline_missing":rs="not_comparable";sc["not_triggered"]+=1
        else:rs="not_triggered";sc[rs]+=1
        rows.append({"ticker":d["ticker"],"metric_name":d["metric_name"],"rule_name":"multi_ticker_threshold","threshold_value":20,"actual_value":dp,"rule_status":rs})
    return {"phase82_multi_ticker_threshold":{"rules_checked":len(rows),"triggered_strengthened":sc["triggered_strengthened"],"triggered_weakened":sc["triggered_weakened"],"triggered_anomaly":sc["triggered_anomaly"],"not_triggered":sc["not_triggered"],"rows":rows,"mock_used":False,"fixture_used":False}}
