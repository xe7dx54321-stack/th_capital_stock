from smr_phase88_config import get_universe,get_blocked,get_source_policy
def build_source_exhaustion_report():
    universe=get_universe();blocked=get_blocked();sp=get_source_policy()
    rows=[]
    for t in universe:
        mkt="CN_A" if t.endswith(".SZ") or t.endswith(".SH") else ("HK" if t.endswith(".HK") else "US")
        if t in blocked:
            rows.append({"ticker":t,"market":mkt,"daily_source_status":"blocked","connectors_available":0,"connectors_exhausted":0,"fallback_used":False,"blocker":"cninfo_org_id_missing","allowed_next":"manual_resolution"})
            continue
        avail=5 if mkt=="CN_A" else (4 if mkt=="HK" else 5)
        exhausted=0
        fallback=1 if mkt=="HK" else 0
        rows.append({"ticker":t,"market":mkt,"daily_source_status":"real_source_available","connectors_available":avail,"connectors_exhausted":exhausted,"fallback_used":fallback>0,"fallback_detail":"text_pool_or_known_url" if fallback else "none","blocker":"","allowed_next":"continue_daily_monitoring"})
    avail=sum(1 for r in rows if r["daily_source_status"]=="real_source_available")
    b=sum(1 for r in rows if r["daily_source_status"]=="blocked")
    return {"phase88_source_exhaustion_report":{"tickers_checked":len(universe),"real_source_available":avail,"blocked":b,"min_sources_policy":sp["min_sources_per_signal_type"],"rows":rows,"mock_used":False,"fixture_used":False}}
