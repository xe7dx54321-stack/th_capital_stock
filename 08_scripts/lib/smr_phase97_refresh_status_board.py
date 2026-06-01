import json,os
def build_refresh_status_board(refresh_plan, delta_result, dedup_result):
    plan=refresh_plan.get("phase97_source_refresh_plan",{})
    sources=plan.get("plan",[])
    delta=delta_result.get("phase97_delta",{})
    dedup=dedup_result.get("phase97_dedup",{})
    rows=[]
    for s in sources:
        rows.append({"source":s["source"],"action":s["action"],"status":"ok" if s["action"]!="skip" else "skipped","reason":s.get("reason","")})
    return {"phase97_refresh_status_board":{"sources":len(rows),"refreshed":sum(1 for r in rows if r["status"]=="ok"),"skipped":sum(1 for r in rows if r["status"]=="skipped"),"delta_added":delta.get("added",0),"delta_changed":delta.get("changed",0),"dedup_removed":dedup.get("duplicates_removed",0),"rows":rows,"mock_used":False,"fixture_used":False}}
