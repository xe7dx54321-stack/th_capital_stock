def build_universe():
    from smr_phase82_coverage_config import load_config
    c=load_config();u=c["universe"];sp=c["source_priority"]
    rows=[{"ticker":t["ticker"],"market":t["market"],"role":t["role"],"coverage_priority":"P0" if t["market"]=="CN_A" else "P1","source_priority":sp.get(t["market"],[]),"expected_blockers":["cninfo_org_id_missing"] if t["ticker"]=="300394.SZ" else([] if t["market"]=="CN_A" else["source_not_supported_for_market"])} for t in u]
    mk={};[mk.setdefault(t["market"],0) for t in u];mk={k:sum(1 for t in u if t["market"]==k) for k in set(t["market"] for t in u)}
    return {"phase82_financial_coverage_universe":{"tickers_total":len(u),"markets":mk,"rows":rows,"mock_used":False,"fixture_used":False}}
