# Phase179 owner review input processing runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase179_review_processing import *

def run_pipeline(mode="dry-run"):
    validator = build_input_schema_validator()
    classifier = build_review_status_classifier()
    revision = build_revision_task_preview()
    daily = build_daily_brief_eligibility()
    weekly = build_weekly_review_eligibility()
    audit = build_review_audit()
    g = build_phase179_guard(); qg = build_phase179_quality_gate(); cc = build_phase179_cannot_conclude_guard()

    v = validator["phase179_schema_validator"]; c = classifier["phase179_review_classifier"]
    return {"phase179_review_processing_pipeline":{
        "mode":mode,"phase":"phase179","strategy":"owner_review_input_processing_and_revision_task_generation",
        "research_only":True,
        "packet_count":9,"owner_review_input_present":v["status"]!="no_input",
        "review_input_state":c["review_input_state"],
        "input_records_loaded":v["input_records_loaded"],
        "valid_review_count":v["valid_review_count"],
        "quarantine_count":v["quarantine_count"],
        "pending_owner_review_count":c["pending"],
        "owner_reviewed_count":c["reviewed"],
        "revision_requested_count":c["revision"],
        "evidence_gap_count":c["evidence_gap"],
        "daily_brief_eligible":c["daily_eligible"],
        "weekly_review_eligible":c["weekly_eligible"],
        "revision_task_preview_count":revision["phase179_revision_task_preview"]["revision_task_count"],
        "guard":g["phase179_guard"]["status"],
        "quality_gate":qg["phase179_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase179_cannot_conclude_guard"]["status"],
        "violations":qg["phase179_quality_gate"]["violations"],
        "owner_review_input_written":False,"auto_signoff":False,"auto_revision":False,
        "review_not_thesis_confirmed":True,"eligibility_not_trade_signal":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase180: Execute packet revisions and integrate into daily research brief."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
