def build_unified_watch_board():
    from smr_phase89_unified_ticker_state import build_unified_ticker_state
    from smr_phase89_opportunity_risk import build_opportunity_risk
    ts=build_unified_ticker_state();op=build_opportunity_risk()
    rows=ts["phase89_unified_ticker_state"]["rows"];op_rows=op["phase89_opportunity_risk"]["rows"]
    sections={"full_coverage":[],"partial_coverage":[],"degraded":[],"blocked":[]}
    for r in rows:
        us=r["unified_status"];t=r["ticker"]
        if us in sections:sections[us].append({"ticker":t,"market":r["market"],"status":us,"degraded":r["degraded_count"],"financial":r["financial"][0]["status"],"valuation":r["valuation"][0]["status"],"pricing":r["pricing"][0]["status"],"expectation":r["expectation"][0]["status"],"external":r["external"][0]["status"],"cannot_conclude":r["cannot_conclude"]})
    return {"phase89_unified_watch_board":{"tickers_total":len(rows),"sections":{k:len(v) for k,v in sections.items()},"rows":rows,"watch_only":True,"not_trade_signal":True,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
