import json,os
from datetime import datetime
def build_refresh_plan(mode="dry-run"):
    now=datetime.now().isoformat()[:10]
    plan=[]
    for src,policy in [
        ("yfinance_financials","daily"),("akshare_sina_financial","daily"),("eastmoney_financial","daily"),
        ("sec_edgar_companyfacts","weekly"),("cninfo_disclosure","skip_blocked"),("szse_disclosure","skip_blocked"),("irm_news","skip_blocked")
    ]:
        action="skip" if "skip" in policy else "refresh"
        if mode=="skip-network": action="skip"
        plan.append({"source":src,"frequency":policy,"action":action,"planned_at":now,"reason":"network_disabled" if mode=="skip-network" else "per_policy"})
    return {"phase97_source_refresh_plan":{"mode":mode,"total_sources":len(plan),"refresh_count":sum(1 for p in plan if p["action"]=="refresh"),"skip_count":sum(1 for p in plan if p["action"]=="skip"),"plan":plan,"mock_used":False,"fixture_used":False}}
