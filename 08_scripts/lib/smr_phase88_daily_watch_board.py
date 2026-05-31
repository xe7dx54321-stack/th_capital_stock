def build_daily_external_watch_board():
    from smr_phase88_daily_delta_engine import build_daily_delta
    from smr_phase88_source_exhaustion import build_source_exhaustion_report
    dd=build_daily_delta();se=build_source_exhaustion_report()
    rows=dd["phase88_daily_delta"]["rows"]
    sections={"new_external_signals":[],"duplicate_signals":[],"stale_or_no_signal":[],"blocked":[]}
    for r in rows:
        if r.get("external_daily_status")=="blocked":sections["blocked"].append(r)
        elif r.get("is_new"):sections["new_external_signals"].append(r)
        elif r.get("is_duplicate"):sections["duplicate_signals"].append(r)
        else:sections["stale_or_no_signal"].append(r)
    return {"phase88_daily_external_watch_board":{"tickers_total":dd["phase88_daily_delta"]["tickers_checked"],"sections":{k:len(v) for k,v in sections.items()},"rows":rows,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
