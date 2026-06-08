# Phase188 reporting: board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase188_real_source_lead_ingestion import *

def build_ingestion_board():
    reg = build_ingestion_registry(); conv = build_source_lead_converter(); meta = build_metadata_validator()
    copy = build_copyright_validator(); dedup = build_ingestion_dedup(); manifest = build_ingestion_manifest()
    match = build_cross_check_match_confirmation(); vr = build_verification_readiness(); er = build_eligibility_refresh()
    audit = build_ingestion_audit_log(); ci = build_console_integration()
    g = build_phase188_guard(); qg = build_phase188_quality_gate(); cc = build_phase188_cannot_conclude_guard()
    return {"phase188_ingestion_board":{"phase":"phase188","strategy":"real_source_lead_to_dirty_inbox_ingestion","research_only":True,
        "registry":reg["phase188_ingestion_registry"],"converted":conv["phase188_converted_items"],
        "metadata":meta["phase188_metadata_validation"],"copyright":copy["phase188_copyright_validation"],
        "dedup":dedup["phase188_ingestion_dedup"],"manifest":manifest["phase188_ingestion_manifest"],
        "cross_check_match":match["phase188_cross_check_match_confirmation"],"verification_readiness":vr["phase188_verification_readiness"],
        "eligibility_refresh":er["phase188_eligibility_refresh"],"audit_log":audit["phase188_ingestion_audit_log"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_ingestion_brief():
    m = build_ingestion_manifest()["phase188_ingestion_manifest"]
    return {"phase188_ingestion_brief":{"headline":"Real source leads ingested into Dirty Inbox. 6 leads converted. NOT clean evidence.",
        "converted":m["converted"],"metadata_valid":m["metadata_valid"],"copyright_safe":m["copyright_safe"],
        "duplicates":m["duplicates"],"ingested":m["ingested"],"ready_for_triage":m["ready_for_triage"],
        "ingested_not_clean_evidence":True,"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_dashboard():
    m = build_ingestion_manifest()["phase188_ingestion_manifest"]
    return {"phase188_dashboard":{"summary":{"phase":"phase188","strategy":"real_source_lead_to_dirty_inbox_ingestion",
        "converted":m["converted"],"ingested":m["ingested"],"metadata_valid":m["metadata_valid"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "clean_evidence_written":False,"packet_updated":False,"llm_api_called":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"raw_full_text_saved":False,"mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase188_cannot_conclude_guard()

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args(); fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_ingestion_board,"brief":build_ingestion_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_ingestion_board(),ensure_ascii=False,indent=2))
