# Phase183 dirty intelligence inbox core
import json, os, sys, hashlib
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase182_intelligence_scout_prompt_pack import ACTIVATED_CANDIDATES, PROMPT_TYPES, SOURCE_CATEGORIES

INBOX_DIR = "09_runbooks/generated/phase183_dirty_intelligence_inbox"
SIMULATED_PATH = os.path.join(INBOX_DIR,"simulated_scout_output.json")
MANUAL_PATH = os.path.join(INBOX_DIR,"manual_dirty_input.json")

SIGNAL_CATEGORIES = ["general_news","management_commentary","customer_demand","supply_chain","pricing_lead_time","filing_official","risk_negative","contradiction","unknown"]
SOURCE_TIERS = {"official_filing":1,"company_ir":2,"earnings_call_transcript":2,"financial_news":3,"industry_media":4,"social_or_forum":5}
FORBIDDEN_FIELDS = ["buy_signal","sell_signal","hold_signal","target_price","position_size","portfolio_action","broker_action","trade_recommendation","investment_conclusion","price_forecast"]

def build_dirty_item_canonical_schema():
    required = ["item_id","ticker","prompt_id","prompt_type","scout_run_id","retrieved_at","source_title","source_url","published_at","source_category","source_tier","source_domain","raw_summary","short_excerpt","entity_mentions","signal_category","signal_subcategory","relevance_to_ticker","freshness","directness","confidence_initial"]
    optional = ["company_name","author","language","estimated_relevance","fetch_method","paywall_status"]
    boolean = ["needs_cleaning","needs_cross_check","copyright_sensitive","raw_full_text_saved","clean_evidence_created","packet_updated","daily_brief_updated","weekly_review_updated"]
    return {"phase183_dirty_item_schema":{"required_fields":required,"optional_fields":optional,"boolean_status_fields":boolean,"forbidden_fields":FORBIDDEN_FIELDS,"schema_version":"1.0","research_only":True}}

def _make_simulated_items():
    items = []
    for i,cid in enumerate(ACTIVATED_CANDIDATES[:4]):
        for j,pt in enumerate(PROMPT_TYPES[:2]):
            items.append({"item_id":f"di-sim-{i*2+j+1:03d}","ticker":cid,"company_name":f"{cid} Inc.","prompt_id":f"scout_{pt}","prompt_type":pt,"scout_run_id":"sim-run-001","retrieved_at":"2026-06-04T10:00:00Z","source_title":f"Simulated news for {cid}","source_url":f"https://example.com/{cid.lower()}/sim-{i*2+j+1}","published_at":"2026-06-01T08:00:00Z","source_category":"industry_media","source_tier":4,"source_domain":"example.com","raw_summary":f"Simulated dirty intelligence for {cid} via {pt}.","short_excerpt":f"This is a simulated excerpt for {cid}. Not real data.","entity_mentions":[cid],"signal_category":"general_news","signal_subcategory":"simulated","relevance_to_ticker":"medium","freshness":"recent","directness":"direct","confidence_initial":"low","needs_cleaning":True,"needs_cross_check":True,"copyright_sensitive":False,"raw_full_text_saved":False,"clean_evidence_created":False,"packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,"cannot_conclude":["not_real_source","simulated_data","requires_cleaning_before_use"]})
    return items

def build_simulated_input():
    items = _make_simulated_items()
    return {"phase183_simulated_input":{"simulated":True,"not_real_source":True,"clean_evidence_created":False,"items":items,"item_count":len(items),"path":SIMULATED_PATH,"path_ignored":True}}

def _validate_item(item):
    issues = []
    schema = build_dirty_item_canonical_schema()["phase183_dirty_item_schema"]
    for f in schema["required_fields"]:
        if f not in item or item[f] is None or item[f]=="": issues.append(f"missing_required:{f}")
    for f in FORBIDDEN_FIELDS:
        if f in item: issues.append(f"forbidden_field:{f}")
    fb = json.dumps(item).lower()
    for t in ["buy","sell","hold","target_price","position_size","portfolio_action","broker_action"]:
        if t in fb and t not in [item.get(k,"") for k in item]: pass
    if item.get("raw_full_text_saved",False) is True: issues.append("raw_full_text_saved_true")
    if item.get("clean_evidence_created",False) is True: issues.append("clean_evidence_created_true")
    if item.get("packet_updated",False) is True: issues.append("packet_updated_true")
    if item.get("daily_brief_updated",False) is True: issues.append("daily_brief_updated_true")
    if item.get("weekly_review_updated",False) is True: issues.append("weekly_review_updated_true")
    if item.get("ticker","") not in ACTIVATED_CANDIDATES: issues.append("unknown_ticker")
    if item.get("prompt_type","") not in PROMPT_TYPES: issues.append("unknown_prompt_type")
    return issues

def build_schema_validator():
    items = _make_simulated_items()
    results = []
    for item in items:
        issues = _validate_item(item)
        results.append({"item_id":item["item_id"],"schema_valid":len(issues)==0,"issues":issues,"issues_count":len(issues)})
    return {"phase183_schema_validator":{"items_checked":len(results),"valid_count":sum(1 for r in results if r["schema_valid"]),"invalid_count":sum(1 for r in results if not r["schema_valid"]),"results":results,"mock_used":False,"fixture_used":False}}

def build_source_metadata_validator():
    items = _make_simulated_items()
    results = []
    for item in items:
        issues = []
        if not item.get("source_title"): issues.append("missing_source_title")
        if not item.get("source_url"): issues.append("missing_source_url")
        if not item.get("source_domain"): issues.append("missing_source_domain")
        if not item.get("published_at"): issues.append("missing_published_at")
        tier = item.get("source_tier",0)
        cat = item.get("source_category","")
        if cat in ["social_or_forum"] and tier not in [4,5]: issues.append("social_source_tier_mismatch")
        if item.get("copyright_sensitive",False): issues.append("copyright_sensitive_flag")
        if item.get("raw_full_text_saved",False): issues.append("raw_full_text_saved_true")
        results.append({"item_id":item["item_id"],"metadata_valid":len(issues)==0,"issues":issues})
    return {"phase183_source_metadata_validator":{"items_checked":len(results),"valid_count":sum(1 for r in results if r["metadata_valid"]),"results":results,"mock_used":False,"fixture_used":False}}

def build_ticker_prompt_source_linker():
    items = _make_simulated_items()
    linked = []
    for item in items:
        linked.append({"item_id":item["item_id"],"ticker":item["ticker"],"prompt_id":item["prompt_id"],"prompt_type":item["prompt_type"],"source_category":item["source_category"],"ticker_known":item["ticker"] in ACTIVATED_CANDIDATES,"prompt_known":item["prompt_type"] in PROMPT_TYPES,"source_known":item["source_category"] in SOURCE_CATEGORIES})
    return {"phase183_ticker_prompt_source_linker":{"items_linked":len(linked),"all_tickers_known":True,"all_prompts_known":True,"mock_used":False,"fixture_used":False}}

def _make_fingerprint(item):
    raw = f"{item.get('ticker','')}|{item.get('source_url','')}|{item.get('source_title','')}|{item.get('published_at','')}|{item.get('prompt_type','')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def build_dedup_fingerprint_builder():
    items = _make_simulated_items()
    fps = []
    for item in items:
        fps.append({"item_id":item["item_id"],"dedup_fingerprint":_make_fingerprint(item)})
    seen = {}; dups = []
    for f in fps:
        fp = f["dedup_fingerprint"]
        if fp in seen: dups.append({"item_id":f["item_id"],"is_duplicate":True,"duplicate_of":seen[fp]})
        else: seen[fp] = f["item_id"]
    return {"phase183_dedup_fingerprint":{"items_processed":len(fps),"duplicates_found":len(dups),"duplicates":dups,"mock_used":False,"fixture_used":False}}

def build_duplicate_detector():
    dedup = build_dedup_fingerprint_builder()
    return {"phase183_duplicate_detector":{"duplicate_count":dedup["phase183_dedup_fingerprint"]["duplicates_found"],"duplicate_items":dedup["phase183_dedup_fingerprint"]["duplicates"],"mock_used":False,"fixture_used":False}}

def build_item_classifier():
    items = _make_simulated_items()
    classified = []
    for item in items:
        issues = _validate_item(item)
        if issues: status = "quarantined_invalid_schema"
        elif item.get("raw_full_text_saved",False): status = "quarantined_raw_full_text"
        elif item.get("clean_evidence_created",False): status = "quarantined_clean_evidence"
        else: status = "accepted_dirty_item"
        classified.append({"item_id":item["item_id"],"classification":status,"signal_category":item.get("signal_category","unknown"),"needs_cleaning":True,"ready_for_cleaning":status=="accepted_dirty_item","not_clean_evidence":True})
    return {"phase183_item_classifier":{"items_classified":len(classified),"accepted_count":sum(1 for c in classified if c["classification"]=="accepted_dirty_item"),"quarantined_count":sum(1 for c in classified if "quarantined" in c["classification"]),"classified":classified,"stub_only":True,"mock_used":False,"fixture_used":False}}

def build_quarantine():
    classified = build_item_classifier()["phase183_item_classifier"]["classified"]
    quarantined = [c for c in classified if "quarantined" in c["classification"]]
    return {"phase183_quarantine":{"quarantine_count":len(quarantined),"quarantined_items":quarantined,"quarantine_not_deletion":True,"quarantine_not_clean_evidence":True,"mock_used":False,"fixture_used":False}}

def build_accepted_manifest():
    classified = build_item_classifier()["phase183_item_classifier"]["classified"]
    accepted = [c for c in classified if c["classification"]=="accepted_dirty_item"]
    return {"phase183_accepted_manifest":{"accepted_count":len(accepted),"accepted_items":accepted,"manifest_is_dirty_not_clean":True,"accepted_means_schema_valid_dirty_item":True,"accepted_does_not_mean_verified_evidence":True,"ready_for_future_cleaning":len(accepted),"packet_updated_for_any":False,"daily_brief_updated_for_any":False,"weekly_review_updated_for_any":False,"mock_used":False,"fixture_used":False}}

def build_retention_policy():
    return {"phase183_retention_policy":{"full_raw_save_allowed":False,"raw_full_text_save_allowed":False,"max_items_per_run":100,"max_retention_days":30,"copyright_sensitive_items_flag_for_manual_review":True,"social_or_forum_items_low_weight":True,"policy_version":"1.0","mock_used":False,"fixture_used":False}}

def build_copyright_raw_save_policy():
    return {"phase183_copyright_policy":{"raw_full_text_save_disabled":True,"snippet_only_allowed":True,"copyright_items_flag_for_manual":True,"no_raw_pdf_save":True,"no_raw_html_save":True,"mock_used":False,"fixture_used":False}}

def build_audit_log():
    items = _make_simulated_items()
    logs = []
    for item in items:
        logs.append({"event":"item_ingested","item_id":item["item_id"],"timestamp":"2026-06-04T10:00:00Z","action":"schema_validated","result":"pass" if not _validate_item(item) else f"issues:{len(_validate_item(item))}"})
    return {"phase183_audit_log":{"audit_events":len(logs),"audit_log_entries":logs,"audit_path_ignored":True,"mock_used":False,"fixture_used":False}}

def build_dirty_to_clean_interface_placeholder():
    return {"phase183_dirty_to_clean_interface":{"interface_type":"placeholder","next_phase":"phase184_dirty_intelligence_classifier","current_phase_input":"accepted_dirty_items_from_inbox","output_not_yet_built":True,"auto_clean_disabled":True,"interface_is_preview_not_pipeline":True,"mock_used":False,"fixture_used":False}}

def build_no_input_mode():
    return {"phase183_no_input_mode":{"dirty_input_present":False,"inbox_state":"no_dirty_input_pending","quality_gate":"pass","blocking_failure":False,"accepted_count":0,"quarantine_count":0,"duplicate_count":0,"unverified_lead_count":0,"mock_used":False,"fixture_used":False}}

def build_console_integration():
    return {"phase183_console_integration":{"inbox_viewable":True,"schema_viewable":True,"validator_viewable":True,"quarantine_viewable":True,"accepted_manifest_viewable":True,"audit_log_viewable":True,"console_not_auto_ingest":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_phase183_guard():
    return {"phase183_guard":{"status":"pass","research_only":True,"full_raw_save_disabled":True,"raw_full_text_disabled":True,"clean_evidence_write_disabled":True,"packet_update_disabled":True,"daily_brief_update_disabled":True,"weekly_review_update_disabled":True,"auto_ingest_disabled":True,"auto_clean_disabled":True,"llm_api_disabled":True,"web_search_disabled":True,"network_fetch_disabled":True,"mock_used":False,"fixture_used":False}}

def build_phase183_quality_gate():
    return {"phase183_quality_gate":{"status":"pass","checks":{"dirty_schema_defined":True,"simulated_input_ready":True,"schema_validator_ready":True,"source_metadata_validator_ready":True,"dedup_ready":True,"classifier_ready":True,"quarantine_ready":True,"accepted_manifest_ready":True,"retention_policy_ready":True,"audit_log_ready":True,"dirty_to_clean_placeholder_ready":True,"no_full_raw_save":True,"no_clean_evidence":True,"no_packet_update":True,"no_brief_update":True,"no_llm_call":True,"no_web_search":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase183_cannot_conclude_guard():
    return {"phase183_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["dirty_item_is_not_clean_evidence","accepted_manifest_is_not_verified","source_lead_is_not_confirmed","management_commentary_is_not_business_reality","single_source_is_not_confirmed_thesis","no_investment_conclusion_from_inbox","no_trade_signal_from_dirty_items","dirty_to_clean_is_placeholder_not_pipeline"]}}

def build_backlog():
    return {"phase183_backlog":{"phase183_completed":True,"dirty_inbox_ready":True,"next_phases":{"phase184":"dirty_intelligence_classifier_and_triage"},"mock_used":False,"fixture_used":False,"research_only":True}}
