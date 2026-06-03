import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_source_request_adapter import probe_url

def probe_news_event_sources(skip_network=False):
    sources=[{"source_id":"hkex_news","probe_url":"https://www.hkexnews.hk","tickers":["09988.HK","00700.HK"],"market":"HK"},{"source_id":"finviz_news","probe_url":"https://finviz.com","tickers":["NVDA","AVGO"],"market":"US"}]
    results=[]
    for s in sources:
        r={"source_id":s["source_id"],"type":"news_event","market":s["market"],"tickers":s["tickers"]}
        if skip_network:
            r["probe_status"]="skipped"; r["reachable"]=False; r["note"]="skip_network_mode"
        else:
            pr=probe_url(s["probe_url"])
            r["probe_status"]=pr["status"]; r["reachable"]=pr["reachable"]; r["http_code"]=pr["http_code"]
            if pr["error"]: r["error"]=pr["error"]
        results.append(r)
    available=sum(1 for r in results if r.get("probe_status")=="available")
    return {"phase128_news_event_probe":{"total":len(results),"available":available,"blocked":len(results)-available,"skipped":sum(1 for r in results if r.get("probe_status")=="skipped"),"results":results,"mock_used":False,"fixture_used":False,"raw_saved":False}}
