def build_daily_external_integration():
    from smr_phase88_daily_delta_engine import build_daily_delta
    from smr_phase88_source_exhaustion import build_source_exhaustion_report
    dd=build_daily_delta();se=build_source_exhaustion_report()
    d=dd["phase88_daily_delta"];e=se["phase88_source_exhaustion_report"]
    return {"phase88_daily_external_integration":{"tickers_checked":d["tickers_checked"],"external_texts_checked":d["external_texts_checked"],"new_signals":d["external_new_signals"],"duplicate_signals":d["external_duplicate_signals"],"real_source_available":e["real_source_available"],"blocked":e["blocked"],"history_enabled":d["history_enabled"],"rows":d["rows"],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
