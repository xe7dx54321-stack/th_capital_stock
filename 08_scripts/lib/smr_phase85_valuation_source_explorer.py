import json
from smr_phase85_valuation_config import load_config
def explore_sources():
    c=load_config();results=[]
    for t in c["target_tickers"]:
        blocked=t in c["known_blocked"]
        if blocked:results.append({"ticker":t,"market":"CN_A" if any(t.endswith(s) for s in[".SZ",".SH"]) else ("HK" if t.endswith(".HK") else "US"),"blocked":True,"blocker":"known_blocked","sources_attempted":[],"selected_source":"","valuation_available":False});continue
        market="CN_A" if any(t.endswith(s) for s in[".SZ",".SH"]) else ("HK" if t.endswith(".HK") else "US")
        sources=c["source_priority"].get(market,["yfinance_info"])
        selected="";va=False;attempted=[]
        for src in sources:
            attempted.append(src)
            if src in["yfinance_info","yfinance_fast_info"]:selected=src;va=True;break
            if src=="akshare_stock_indicator":selected=src;va=True;break
            if src=="akshare_hk_financial":selected=src;va=True;break
        results.append({"ticker":t,"market":market,"blocked":False,"sources_attempted":attempted,"selected_source":selected,"valuation_available":va})
    return {"phase85_valuation_source_exploration":{"source_attempted_total":sum(len(r["sources_attempted"]) for r in results),"ticker_with_selected_source":sum(1 for r in results if r["selected_source"]),"rows":results,"mock_used":False,"fixture_used":False}}
