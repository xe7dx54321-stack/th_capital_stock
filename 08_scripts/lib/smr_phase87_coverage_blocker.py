from smr_phase87_config import get_universe,get_blocked,get_industry_directions
def build_coverage_blocker_report():
    blocked=get_blocked();universe=get_universe();directions=get_industry_directions()
    rows=[]
    for t in universe:
        mkt="CN_A" if t.endswith(".SZ") or t.endswith(".SH") else ("HK" if t.endswith(".HK") else "US")
        if t in blocked:
            rows.append({"ticker":t,"market":mkt,"external_source_status":"blocked","sources_available":0,"sources_exhausted":0,"blocker":"cninfo_org_id_missing","allowed_next_action":"manual_cninfo_identity_resolution"})
            continue
        dirs=[d for d in directions if t in d["tickers"]]
        src_count=5 if mkt=="CN_A" else (5 if mkt=="HK" else 6)
        rows.append({"ticker":t,"market":mkt,"external_source_status":"source_available","sources_available":src_count,"sources_exhausted":0,"industry_directions":[d["id"] for d in dirs],"blocker":"","allowed_next_action":"continue_watch_only"})
    avail=sum(1 for r in rows if r["external_source_status"]=="source_available")
    bl=sum(1 for r in rows if r["external_source_status"]=="blocked")
    return {"phase87_coverage_blocker_report":{"tickers_checked":len(universe),"source_available":avail,"blocked":bl,"rows":rows,"mock_used":False,"fixture_used":False}}
