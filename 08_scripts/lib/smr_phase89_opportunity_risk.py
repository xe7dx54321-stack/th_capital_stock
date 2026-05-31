def build_opportunity_risk():
    from smr_phase89_unified_ticker_state import build_unified_ticker_state
    ts=build_unified_ticker_state();rows=ts["phase89_unified_ticker_state"]["rows"]
    results=[];opportunity=0;risk=0;neutral=0;blocked_count=0
    for r in rows:
        cat="neutral"
        us=r["unified_status"]
        if us=="blocked":cat="blocked";blocked_count+=1
        elif us=="full_coverage":cat="monitoring_active";neutral+=1
        elif "partial" in us:cat="partial_monitoring";neutral+=1
        else:cat="degraded_monitoring";risk+=1
        results.append({"ticker":r["ticker"],"market":r["market"],"classification":cat,"unified_status":us,"degraded_count":r["degraded_count"],"cannot_conclude":r["cannot_conclude"],"watch_only":True,"not_trade_signal":True})
    return {"phase89_opportunity_risk":{"tickers_total":len(rows),"active_monitoring":neutral,"degraded":risk,"blocked":blocked_count,"classification_note":"These are monitoring classifications, NOT buy/sell/hold recommendations","no_trade_signal":True,"rows":results,"mock_used":False,"fixture_used":False}}
