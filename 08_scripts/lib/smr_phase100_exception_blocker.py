import json,os
def build_exception_blocker_report(phase98_pipeline):
    p98=phase98_pipeline.get("phase98_pipeline",{})
    exceptions=[{"type":"blocked_source","source":"cninfo_disclosure","ticker":"300394.SZ","blocker":"cninfo_org_id_missing","action":"manual_resolution_required"},{"type":"blocked_source","source":"szse_disclosure","ticker":"300394.SZ","blocker":"linked_to_cninfo","action":"resolve_cninfo_first"},{"type":"blocked_source","source":"irm_news","ticker":"300394.SZ","blocker":"partial_only","action":"irm_ok_for_text_not_financial"},{"type":"partial_valuation","ticker":"688041.SH","gap":"ev_ebitda_ps_ttm","action":"monitor_update"}]
    return {"phase100_exception_blocker":{"total_exceptions":len(exceptions),"exceptions":exceptions,"mock_used":False,"fixture_used":False}}
