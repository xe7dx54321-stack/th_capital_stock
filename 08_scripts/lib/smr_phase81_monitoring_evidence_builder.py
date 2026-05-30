def build_monitoring_evidence(delta,threshold,config):
    rows=[];dr={r["metric_name"]:r for r in delta["phase81_signal_delta"]["rows"]}
    cc=config["signals"]
    for mn in["revenue","gross_margin","R&D_expense","net_profit","operating_cash_flow"]:
        d=dr.get(mn,{});c=cc.get(mn,{});nc=c.get("cannot_conclude",[])
        ds=d.get("delta_status","not_comparable")
        if ds=="strengthened":et="threshold_strengthened_observed";ct=f"{mn}_growth_strengthened";lim=f"{mn} trend strengthened, does not confirm claims beyond metric trend."
        elif ds=="weakened":et="threshold_weakened_observed";ct=f"{mn}_weakened";lim=f"{mn} weakened, does not confirm claims beyond metric trend."
        elif ds=="unchanged":et="unchanged_signal_observed";ct=f"{mn}_unchanged";lim=f"{mn} stable, does not confirm new developments."
        elif ds=="baseline_missing":et="baseline_missing_observed";ct=f"{mn}_baseline_missing";lim=f"{mn} baseline unavailable, monitoring suspended.";nc=[]
        else:et="not_comparable";ct=f"{mn}_not_comparable";lim=f"{mn} not comparable."
        rows.append({"metric_name":mn,"evidence_type":et,"claim_type":ct,"limitation":lim,"cannot_conclude":nc})
    return {"phase81_monitoring_evidence":{"ticker":"688041.SH","monitoring_evidence_created":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
