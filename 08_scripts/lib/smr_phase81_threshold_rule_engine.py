def run_threshold_rules(delta,config):
    rows=[];sc={"triggered_strengthened":0,"triggered_weakened":0,"triggered_anomaly":0,"not_triggered":0}
    th=config["signals"];dr={r["metric_name"]:r for r in delta["phase81_signal_delta"]["rows"]}
    for mn,sv in th.items():
        if not sv["enabled"]:continue
        tr=sv["thresholds"];d=dr.get(mn,{})
        if d.get("delta_status")=="baseline_missing":
            for rn,rv in tr.items():
                rows.append({"metric_name":mn,"rule_name":rn,"threshold_value":rv,"actual_value":None,"rule_status":"not_comparable","explanation":"baseline_missing"});sc["not_triggered"]+=1
            continue
        for rn,rv in tr.items():
            av=None;rs="not_triggered"
            if rn.startswith("strengthened"):
                if mn=="gross_margin":av=d.get("delta_pct_point");rs="triggered_strengthened" if av and av>=rv else "not_triggered"
                else:av=d.get("delta_pct");rs="triggered_strengthened" if av and av>=rv else "not_triggered"
            elif rn.startswith("weakened"):
                if mn=="gross_margin":av=d.get("delta_pct_point");rs="triggered_weakened" if av is not None and av<=rv else "not_triggered"
                else:av=d.get("delta_pct");rs="triggered_weakened" if av is not None and av<=rv else "not_triggered"
            elif rn.startswith("anomaly"):
                if mn=="gross_margin":av=abs(d.get("delta_pct_point",0));rs="triggered_anomaly" if av>=rv else "not_triggered"
                else:av=abs(d.get("delta_pct",0));rs="triggered_anomaly" if av>=rv else "not_triggered"
            sc[rs]=sc.get(rs,0)+1;exp=f"delta {av} vs threshold {rv} = {rs}"
            rows.append({"metric_name":mn,"rule_name":rn,"threshold_value":rv,"actual_value":av,"rule_status":rs,"explanation":exp})
    return {"phase81_threshold_rule":{"ticker":"688041.SH","rules_checked":len(rows),"triggered_strengthened":sc["triggered_strengthened"],"triggered_weakened":sc["triggered_weakened"],"triggered_anomaly":sc["triggered_anomaly"],"not_triggered":sc["not_triggered"],"rows":rows,"mock_used":False,"fixture_used":False}}
