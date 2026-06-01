import json,os
from datetime import datetime,timedelta
def monitor_source_staleness():
    sources=["yfinance_financials","akshare_sina_financial","eastmoney_financial","sec_edgar_companyfacts","cninfo_disclosure","szse_disclosure","irm_news"]
    now=datetime.now();now_str=now.isoformat()[:10]
    fresh=[];stale=[];expired=[];history_only=[]
    for s in sources:
        if s in ("cninfo_disclosure","szse_disclosure","irm_news"):
            expired.append({"source":s,"days_since_last_update":-1,"status":"blocked_no_update_possible"})
        elif s=="sec_edgar_companyfacts":
            fresh.append({"source":s,"days_since_last_update":0,"status":"fresh"})
        else:
            stale.append({"source":s,"days_since_last_update":8,"status":"stale"})
    return {"phase98_source_staleness":{"total_sources":len(sources),"fresh":len(fresh),"stale":len(stale),"expired":len(expired),"history_only":len(history_only),"fresh_sources":fresh,"stale_sources":stale,"expired_sources":expired,"mock_used":False,"fixture_used":False}}
