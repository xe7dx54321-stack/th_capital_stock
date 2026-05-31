from smr_phase89_config import get_universe,get_blocked,get_gaps
def build_unified_ticker_state():
    universe=get_universe();blocked=get_blocked();gaps=get_gaps();states=[]
    for t in universe:
        mkt="CN_A" if t.endswith(".SZ") or t.endswith(".SH") else ("HK" if t.endswith(".HK") else "US")
        if t in blocked:
            states.append({"ticker":t,"market":mkt,"unified_status":"blocked","financial":[{"status":"blocked","blocker":"cninfo_org_id_missing"}],"valuation":[{"status":"blocked","blocker":"cninfo_org_id_missing"}],"pricing":[{"status":"blocked","blocker":"cninfo_org_id_missing"}],"expectation":[{"status":"blocked","blocker":"cninfo_org_id_missing"}],"external":[{"status":"blocked","blocker":"cninfo_org_id_missing"}],"cannot_conclude":["full_coverage_blocked_by_cninfo_org_id"],"subsystem_count":5,"degraded_count":5})
            continue
        tg=gaps.get(t,[])
        fin_status="available";val_status="available" if "valuation_unavailable" not in tg else "unavailable";prc_status="available" if "pricing_unavailable" not in tg else "unavailable";exp_status="available";ext_status="available"
        degraded=sum(1 for x in [val_status,prc_status] if x=="unavailable")
        us="full_coverage" if degraded==0 else ("partial_coverage" if degraded<2 else "degraded_coverage")
        states.append({"ticker":t,"market":mkt,"unified_status":us,"financial":[{"status":fin_status,"blocker":""}],"valuation":[{"status":val_status,"blocker":"valuation_unavailable" if val_status=="unavailable" else ""}],"pricing":[{"status":prc_status,"blocker":"pricing_unavailable_yfinance_404" if prc_status=="unavailable" else ""}],"expectation":[{"status":exp_status,"blocker":""}],"external":[{"status":ext_status,"blocker":""}],"cannot_conclude":["unified_status_not_trade_signal","degraded_not_equal_to_sell","gap_not_equal_to_opportunity_loss"],"subsystem_count":5,"degraded_count":degraded})
    full=sum(1 for s in states if s["unified_status"]=="full_coverage");partial=sum(1 for s in states if s["unified_status"]=="partial_coverage");degraded_sum=sum(1 for s in states if s["unified_status"]=="degraded_coverage");bl=sum(1 for s in states if s["unified_status"]=="blocked")
    return {"phase89_unified_ticker_state":{"tickers_total":len(universe),"full_coverage":full,"partial_coverage":partial,"degraded":degraded_sum,"blocked":bl,"known_gaps_preserved":list(gaps.keys()),"rows":states,"mock_used":False,"fixture_used":False}}
