def build_external_integration():
    from smr_phase87_external_evidence import build_external_evidence
    from smr_phase87_coverage_blocker import build_coverage_blocker_report
    ev=build_external_evidence();bl=build_coverage_blocker_report()
    eb=ev["phase87_external_evidence"];cb=bl["phase87_coverage_blocker_report"]
    return {"phase87_external_integration":{"tickers_checked":eb["tickers_checked"],"evidence_entries":eb["evidence_entries"],"source_available":cb["source_available"],"blocked":cb["blocked"],"avg_reliability":round(sum(r.get("reliability_score",0) or 0 for r in eb["rows"])/max(len(eb["rows"]),1),2),"rows":eb["rows"],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
