import json,os
from datetime import datetime
def build_source_health_registry():
    sources=["yfinance_financials","akshare_sina_financial","eastmoney_financial","sec_edgar_companyfacts","cninfo_disclosure","szse_disclosure","irm_news"]
    rows=[]
    for s in sources:
        rows.append({"source":s,"health_status":"pending_heartbeat","last_heartbeat_at":None,"last_heartbeat_result":None,"consecutive_failures":0,"notes":""})
    return {"phase98_source_health_registry":{"sources_monitored":len(sources),"health_status_summary":{"healthy":0,"warning":0,"degraded":0,"critical":0,"blocked":3},"rows":rows,"mock_used":False,"fixture_used":False}}
