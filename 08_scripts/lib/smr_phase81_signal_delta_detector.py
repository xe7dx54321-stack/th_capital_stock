def detect_delta(baselines,config):
    rows=[];sc={"strengthened":0,"weakened":0,"unchanged":0,"baseline_missing":0}
    th=config["signals"]
    for b in baselines["phase81_signal_baseline"]["rows"]:
        m=b["metric_name"];tr=th.get(m,{}).get("thresholds",{})
        if not b["baseline_available"]:ds="baseline_missing";rs="no_baseline";sc[ds]+=1;rows.append({"metric_name":m,"baseline_period":"","latest_period":b.get("latest_period",""),"delta_value":0,"delta_pct":0.0,"delta_status":ds,"reason":rs})
        elif m=="gross_margin":
            dp=b["latest_value"]-b["baseline_value"];s_up=tr.get("strengthened_delta_pct_point",3.0);s_dn=tr.get("weakened_delta_pct_point",-3.0)
            if dp>=s_up:ds="strengthened";rs="delta_above_strengthened_threshold"
            elif dp<=s_dn:ds="weakened";rs="delta_below_weakened_threshold"
            else:ds="unchanged";rs="delta_within_threshold"
            sc[ds]+=1;rows.append({"metric_name":m,"baseline_period":b["baseline_period"],"latest_period":b["latest_period"],"delta_pct_point":round(dp,2),"delta_status":ds,"reason":rs})
        else:
            dp=b["latest_value"]-b["baseline_value"];dpp=round(dp/b["baseline_value"]*100,2) if b["baseline_value"] else 0
            s_up=tr.get("strengthened_yoy_pct",20.0);s_dn=tr.get("weakened_yoy_pct",-10.0)
            if dpp>=s_up:ds="strengthened";rs="delta_above_strengthened_threshold"
            elif dpp<=s_dn:ds="weakened";rs="delta_below_weakened_threshold"
            else:ds="unchanged";rs="delta_within_threshold"
            sc[ds]+=1;rows.append({"metric_name":m,"baseline_period":b["baseline_period"],"latest_period":b["latest_period"],"delta_value":round(dp,2),"delta_pct":dpp,"delta_status":ds,"reason":rs})
    return {"phase81_signal_delta":{"ticker":"688041.SH","signals_checked":len(baselines["phase81_signal_baseline"]["rows"]),"strengthened":sc["strengthened"],"weakened":sc["weakened"],"unchanged":sc["unchanged"],"baseline_missing":sc["baseline_missing"],"rows":rows,"mock_used":False,"fixture_used":False}}
