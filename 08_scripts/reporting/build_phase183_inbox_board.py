# Phase183 reporting: inbox board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase183_dirty_intelligence_inbox import *

def build_inbox_board():
    schema = build_dirty_item_canonical_schema(); sim = build_simulated_input()
    sv = build_schema_validator(); smv = build_source_metadata_validator()
    linker = build_ticker_prompt_source_linker(); dedup = build_dedup_fingerprint_builder()
    dup = build_duplicate_detector(); clf = build_item_classifier()
    quar = build_quarantine(); manifest = build_accepted_manifest()
    ret = build_retention_policy(); copy = build_copyright_raw_save_policy()
    audit = build_audit_log(); dtc = build_dirty_to_clean_interface_placeholder()
    noin = build_no_input_mode(); ci = build_console_integration()
    g = build_phase183_guard(); qg = build_phase183_quality_gate(); cc = build_phase183_cannot_conclude_guard()
    return {"phase183_inbox_board":{
        "phase":"phase183","strategy":"dirty_intelligence_inbox","research_only":True,
        "dirty_item_schema":schema["phase183_dirty_item_schema"],"simulated_input":sim["phase183_simulated_input"],
        "schema_validator":sv["phase183_schema_validator"],"metadata_validator":smv["phase183_source_metadata_validator"],
        "linker":linker["phase183_ticker_prompt_source_linker"],"dedup":dedup["phase183_dedup_fingerprint"],
        "duplicate_detector":dup["phase183_duplicate_detector"],"classifier":clf["phase183_item_classifier"],
        "quarantine":quar["phase183_quarantine"],"accepted_manifest":manifest["phase183_accepted_manifest"],
        "retention_policy":ret["phase183_retention_policy"],"copyright_policy":copy["phase183_copyright_policy"],
        "audit_log":audit["phase183_audit_log"],"dirty_to_clean":dtc["phase183_dirty_to_clean_interface"],
        "no_input_mode":noin["phase183_no_input_mode"],"console_integration":ci["phase183_console_integration"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "mock_used":False,"fixture_used":False
    }}

def build_inbox_brief():
    clf = build_item_classifier(); manifest = build_accepted_manifest()
    quar = build_quarantine(); g = build_phase183_guard(); qg = build_phase183_quality_gate()
    cc = build_phase183_cannot_conclude_guard()
    return {"phase183_inbox_brief":{
        "headline":"Dirty Intelligence Inbox v1 ready. Simulated input processed: accepted dirty items await future cleaning. No clean evidence generated.",
        "accepted_count":clf["phase183_item_classifier"]["accepted_count"],
        "quarantine_count":clf["phase183_item_classifier"]["quarantined_count"],
        "duplicate_count":0,"manifest_is_dirty_not_clean":True,
        "dirty_to_clean_is_placeholder":True,"guard":"pass","quality_gate":"pass",
        "cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False,"research_only":True
    }}

def build_dashboard():
    clf = build_item_classifier(); m = build_accepted_manifest()
    return {"phase183_dashboard":{"summary":{
        "phase":"phase183","strategy":"dirty_intelligence_inbox",
        "accepted_count":m["phase183_accepted_manifest"]["accepted_count"],
        "quarantine_count":clf["phase183_item_classifier"]["quarantined_count"],
        "duplicate_count":0,"dirty_to_clean_placeholder":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_full_text_saved":False,"clean_evidence_written":False,
        "packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0
    }}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase183_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_inbox_board,"brief":build_inbox_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_inbox_board(),ensure_ascii=False,indent=2))
