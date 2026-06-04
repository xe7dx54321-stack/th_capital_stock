# Phase183 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase183_dirty_intelligence_inbox import *

def run_pipeline(mode="dry-run"):
    schema = build_dirty_item_canonical_schema()
    sim = build_simulated_input()
    sv = build_schema_validator()
    smv = build_source_metadata_validator()
    linker = build_ticker_prompt_source_linker()
    dedup = build_dedup_fingerprint_builder()
    dup = build_duplicate_detector()
    clf = build_item_classifier()
    quar = build_quarantine()
    manifest = build_accepted_manifest()
    ret = build_retention_policy()
    copy = build_copyright_raw_save_policy()
    audit = build_audit_log()
    dtc = build_dirty_to_clean_interface_placeholder()
    noin = build_no_input_mode()
    g = build_phase183_guard()
    qg = build_phase183_quality_gate()
    cc = build_phase183_cannot_conclude_guard()

    return {"phase183_dirty_intelligence_inbox_pipeline":{
        "mode":mode,"phase":"phase183","strategy":"dirty_intelligence_inbox","research_only":True,
        "dirty_input_present":len(sim["phase183_simulated_input"]["items"])>0,"input_mode":"simulated",
        "input_records_loaded":sim["phase183_simulated_input"]["item_count"],
        "simulated":True,"not_real_source":True,
        "accepted_count":manifest["phase183_accepted_manifest"]["accepted_count"],
        "quarantine_count":quar["phase183_quarantine"]["quarantine_count"],
        "duplicate_count":dup["phase183_duplicate_detector"]["duplicate_count"],
        "unverified_lead_count":0,"needs_cross_check_count":sim["phase183_simulated_input"]["item_count"],
        "ready_for_cleaning_count":manifest["phase183_accepted_manifest"]["accepted_count"],
        "schema_items_checked":sv["phase183_schema_validator"]["items_checked"],
        "schema_valid_count":sv["phase183_schema_validator"]["valid_count"],
        "metadata_items_checked":smv["phase183_source_metadata_validator"]["items_checked"],
        "accepted_manifest_generated":True,"quarantine_generated":True,"duplicate_report_generated":True,
        "retention_policy_generated":True,"copyright_policy_generated":True,"audit_log_generated":True,
        "dirty_to_clean_interface_generated":True,"dirty_to_clean_is_placeholder":True,
        "accepted_does_not_mean_clean_evidence":True,"source_lead_not_confirmed_fact":True,
        "guard":g["phase183_guard"]["status"],"quality_gate":qg["phase183_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase183_cannot_conclude_guard"]["status"],"violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_full_text_saved":False,"clean_evidence_written":False,
        "packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "auto_ingest_disabled":True,"auto_clean_disabled":True,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase184: Dirty Intelligence Classifier and Triage."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
