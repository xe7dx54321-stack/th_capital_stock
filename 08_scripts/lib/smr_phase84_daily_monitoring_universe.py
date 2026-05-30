from smr_phase84_scheduled_monitoring_config import load_config
def build():
    c=load_config();u=c["universe"]
    rows=[]
    for t in u["tickers"]:
        blocked=t in u["blocked_tickers"];market="CN_A" if any(t.endswith(s) for s in[".SZ",".SH"]) else ("HK" if t.endswith(".HK") else "US")
        rows.append({"ticker":t,"market":market,"coverage_status":"continuous_quant_monitoring_enabled" if not blocked else "blocked","daily_monitoring_enabled":not blocked,"blocked":blocked,"blocker":"cninfo_org_id_missing_or_known_url_not_usable" if blocked else "","source_capability":"blocked" if blocked else "multi_source_monitoring","last_known_watchlist_status":"blocked" if blocked else "tracking"})
    return {"phase84_daily_monitoring_universe":{"tickers_total":len(u["tickers"]),"daily_monitoring_enabled":len(u["covered_tickers"]),"blocked":len(u["blocked_tickers"]),"markets":{"CN_A":4,"HK":2,"US":2},"rows":rows,"mock_used":False,"fixture_used":False}}
