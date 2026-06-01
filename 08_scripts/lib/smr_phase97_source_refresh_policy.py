import json,os
def build_source_refresh_policy():
    policy={
        "yfinance_financials":{"refresh_frequency":"daily","network_required":True,"stale_days":7,"status":"refreshable"},
        "akshare_sina_financial":{"refresh_frequency":"daily","network_required":True,"stale_days":7,"status":"refreshable"},
        "eastmoney_financial":{"refresh_frequency":"daily","network_required":True,"stale_days":7,"status":"refreshable"},
        "sec_edgar_companyfacts":{"refresh_frequency":"weekly","network_required":True,"stale_days":14,"status":"refreshable"},
        "cninfo_disclosure":{"refresh_frequency":"blocked","network_required":True,"stale_days":-1,"status":"stale_ok_skip_refresh","note":"300394 blocker"},
        "szse_disclosure":{"refresh_frequency":"blocked","network_required":True,"stale_days":-1,"status":"stale_ok_skip_refresh"},
        "irm_news":{"refresh_frequency":"blocked","network_required":False,"stale_days":-1,"status":"stale_ok_skip_refresh","note":"partial for 300394 only"},
    }
    return {"phase97_source_refresh_policy":{"sources":len(policy),"refreshable":sum(1 for v in policy.values() if v["status"]=="refreshable"),"blocked":sum(1 for v in policy.values() if v["status"]!="refreshable"),"rows":policy,"mock_used":False,"fixture_used":False}}
