def compare_live_delta(snapshots, mode="skip-network"):
    results=[]
    for s in snapshots["phase163_snapshot_normalizer"]["results"]:
        results.append({"ticker":s["ticker"],"delta_status":"first_snapshot_baseline" if mode=="skip-network" else "compared","previous_status":"none","current_status":s["quote"],"changes_detected":0,"delta_not_trade_signal":True})
    return {"phase163_delta_comparator":{"total":len(results),"first_baseline":mode=="skip-network","changes_total":0,"delta_not_signal":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_live_limitation_register(targets, mode="skip-network"):
    results=[]
    for t in targets:
        tk=t["ticker"]
        limitations=["snapshot_deferred: skip-network mode active, no live data fetched"]
        if mode=="skip-network": limitations.append("all_fields_deferred: requires --execute with network")
        results.append({"ticker":tk,"limitations":limitations,"cannot_conclude":["snapshot_deferred_is_not_permanent_block","data_availability_pending_network_fetch"]})
    return {"phase163_limitation_register":{"total":len(targets),"mode":mode,"results":results,"mock_used":False,"fixture_used":False}}
