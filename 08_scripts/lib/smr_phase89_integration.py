def build_unified_integration():
    from smr_phase89_unified_ticker_state import build_unified_ticker_state
    from smr_phase89_source_health import build_source_health
    from smr_phase89_opportunity_risk import build_opportunity_risk
    ts=build_unified_ticker_state();sh=build_source_health();op=build_opportunity_risk()
    t=ts["phase89_unified_ticker_state"];h=sh["phase89_source_health"];o=op["phase89_opportunity_risk"]
    return {"phase89_unified_integration":{"tickers_total":t["tickers_total"],"full_coverage":t["full_coverage"],"partial":t["partial_coverage"],"degraded":t["degraded"],"blocked":t["blocked"],"source_health_overall":h["overall"],"monitoring_active":o["active_monitoring"],"degraded_risk":o["degraded"],"known_gaps":t["known_gaps_preserved"],"watch_only":True,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
