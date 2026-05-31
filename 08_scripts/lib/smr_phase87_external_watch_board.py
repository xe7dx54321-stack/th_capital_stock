def build_external_watch_board():
    from smr_phase87_external_evidence import build_external_evidence
    from smr_phase87_coverage_blocker import build_coverage_blocker_report
    ev=build_external_evidence();bl=build_coverage_blocker_report()
    eb=ev["phase87_external_evidence"];cb=bl["phase87_coverage_blocker_report"]
    sections={"external_signals_found":[],"external_signals_partial":[],"external_source_blocked":[]}
    for r in eb["rows"]:
        t=r["ticker"]
        if r["evidence_type"]=="external_source_blocked":sections["external_source_blocked"].append({"ticker":t,"market":r["market"],"section":"blocked","blocker":"cninfo_org_id_missing"})
        elif r.get("reliability_score",0) and r.get("reliability_score",0)>=0.7:sections["external_signals_found"].append({"ticker":t,"market":r["market"],"section":"signals_found","industry":r.get("industry_direction",""),"signal_type":r.get("signal_type","")})
        else:sections["external_signals_partial"].append({"ticker":t,"market":r["market"],"section":"partial","industry":r.get("industry_direction","")})
    return {"phase87_external_watch_board":{"tickers_total":eb["tickers_checked"],"sections":{k:len(v) for k,v in sections.items()},"rows":eb["rows"],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
