import json,os
def build_ticker_hard_data_profiles(records):
    """Build per-ticker hard data profile with depth scores."""
    from smr_phase96_config import get_universe
    universe=get_universe()
    profiles={}
    for r in records:
        t=r["ticker"]
        if t not in profiles: profiles[t]={"ticker":t,"categories_covered":set(),"data_types":{},"record_count":0}
        profiles[t]["categories_covered"].add(r["hard_data_category"])
        dt=r.get("data_type","text_evidence");profiles[t]["data_types"][dt]=profiles[t]["data_types"].get(dt,0)+1
        profiles[t]["record_count"]+=1
    rows=[]
    for t in universe:
        p=profiles.get(t,{"ticker":t,"categories_covered":set(),"data_types":{},"record_count":0})
        cats=len(p["categories_covered"])
        depth=min(100,int(cats*15+sum(p["data_types"].values())*2))
        rows.append({"ticker":t,"hard_data_categories":cats,"record_count":p["record_count"],"hard_data_depth_score":depth,"data_types":p["data_types"],"profile_status":"available" if cats>0 else "blocked"})
    return {"phase96_ticker_hard_data_profile":{"tickers_profiled":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
