def build_source_health():
    from smr_phase89_unified_ticker_state import build_unified_ticker_state
    ts=build_unified_ticker_state();rows=ts["phase89_unified_ticker_state"]["rows"]
    health={"financial":{"available":0,"degraded":0,"blocked":0},"valuation":{"available":0,"degraded":0,"blocked":0},"pricing":{"available":0,"degraded":0,"blocked":0},"expectation":{"available":0,"degraded":0,"blocked":0},"external":{"available":0,"degraded":0,"blocked":0}}
    for r in rows:
        for sub in ["financial","valuation","pricing","expectation","external"]:
            sub_data=r.get(sub,[{}])[0] if r.get(sub) else {}
            st=sub_data.get("status","unknown")
            if st=="available":health[sub]["available"]+=1
            elif st=="unavailable":health[sub]["degraded"]+=1
            elif st=="blocked":health[sub]["blocked"]+=1
    return {"phase89_source_health":{"subsystems_checked":5,"tickers_per_subsystem":len(rows),"health_detail":health,"overall":"healthy" if health["financial"]["blocked"]<=1 and health["valuation"]["degraded"]<=2 else "degraded_attention","mock_used":False,"fixture_used":False}}
