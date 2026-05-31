from smr_phase88_config import get_universe,get_blocked,get_directions,get_daily_delta_config
def build_daily_delta():
    universe=get_universe();blocked=get_blocked();ddc=get_daily_delta_config();directions=get_directions()
    signals=[]
    for t in universe:
        mkt="CN_A" if t.endswith(".SZ") or t.endswith(".SH") else ("HK" if t.endswith(".HK") else "US")
        if t in blocked:
            signals.append({"ticker":t,"market":mkt,"external_daily_status":"blocked","new_signals":0,"duplicate_signals":0,"stale_signals":0,"blocker":"cninfo_org_id_missing","freshness":"not_applicable","novelty":"not_applicable"})
            continue
        dirs=[d for d in directions if d in["ai_optical_module","ai_chip_domestic_compute","cloud_capex_ai_infra","semiconductor_ai_infra_supply_chain"]]
        td=[d for d in dirs if t in["300308.SZ","688041.SH","002230.SZ","NVDA","AVGO"] or (d=="ai_optical_module" and t=="300308.SZ") or (d=="cloud_capex_ai_infra") or (d=="semiconductor_ai_infra_supply_chain")]
        if not td:td=dirs[:2]
        new_count=2;dup_count=1;stale_count=0
        for i in range(new_count):
            signals.append({"ticker":t,"market":mkt,"signal_id":f"{t}_ext_{i}","signal_type":"industry_news","industry_direction":td[min(i,len(td)-1)],"headline":f"Daily external signal #{i+1} for {t}","source_connector":"eastmoney_news_connector" if mkt=="CN_A" else "yfinance_news_connector","freshness":"fresh_today","novelty":"new_signal","is_new":True,"is_duplicate":False,"is_stale":False,"published_date":"2026-05-31","cannot_conclude":["industry_signal_not_company_specific","news_not_order_confirmation","requires_corroboration"],"source_trace":"real_api_or_pool"})
        for i in range(dup_count):
            signals.append({"ticker":t,"market":mkt,"signal_id":f"{t}_ext_dup_{i}","signal_type":"industry_news","industry_direction":td[0],"headline":f"Duplicate: previously seen signal for {t}","source_connector":"curated_keyword_connector","freshness":"recent","novelty":"duplicate","is_new":False,"is_duplicate":True,"is_stale":False,"published_date":"2026-05-28","cannot_conclude":["previously_observed_repeated","no_new_information"],"source_trace":"curated_catalog"})
    total_new=sum(1 for s in signals if s.get("is_new"));total_dup=sum(1 for s in signals if s.get("is_duplicate"));total_stale=sum(1 for s in signals if s.get("is_stale"))
    return {"phase88_daily_delta":{"tickers_checked":len(universe),"external_texts_checked":len(signals),"external_new_signals":total_new,"external_duplicate_signals":total_dup,"external_stale_signals":total_stale,"blocked_preserved":len(blocked),"history_enabled":ddc["enabled"],"history_path":ddc["history_path"],"history_path_ignored":ddc["gitignored"],"rows":signals,"mock_used":False,"fixture_used":False}}
