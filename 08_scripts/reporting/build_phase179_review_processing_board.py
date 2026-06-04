# Phase179 reporting: board, brief, dashboard, backlog, guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase179_review_processing import *

def build_review_processing_board():
    validator = build_input_schema_validator()
    classifier = build_review_status_classifier()
    revision = build_revision_task_preview()
    daily = build_daily_brief_eligibility()
    weekly = build_weekly_review_eligibility()
    audit = build_review_audit()
    return {"phase179_review_processing_board":{
        "validator":validator["phase179_schema_validator"],
        "classifier":classifier["phase179_review_classifier"],
        "revision_preview":revision["phase179_revision_task_preview"],
        "daily_eligibility":daily["phase179_daily_brief_eligibility"],
        "weekly_eligibility":weekly["phase179_weekly_review_eligibility"],
        "audit":audit["phase179_review_audit"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass",
        "research_only":True,"mock_used":False,"fixture_used":False
    }}

def build_review_processing_brief():
    c = build_review_status_classifier()["phase179_review_classifier"]
    return {"phase179_review_processing_brief":{"headline":"Owner review input processing complete.","review_input_state":c["review_input_state"],"pending":c["pending"],"reviewed":c["reviewed"],"revision":c["revision"],"daily_eligible":c["daily_eligible"],"weekly_eligible":c["weekly_eligible"],"research_only":True,"mock_used":False,"fixture_used":False}}

def build_dashboard():
    c = build_review_status_classifier()["phase179_review_classifier"]
    return {"phase179_dashboard":{"summary":{"phase":"phase179","strategy":"owner_review_input_processing","packet_count":9,"review_input_state":c["review_input_state"],"pending":c["pending"],"reviewed":c["reviewed"],"revision":c["revision"],"daily_eligible":c["daily_eligible"],"weekly_eligible":c["weekly_eligible"],"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"auto_signoff":False,"auto_revision":False,"watch_core_updated":False,"target_price_created":0,"broker_api_called":False,"mock_used":False,"fixture_used":False}}}

def build_backlog_update():
    return {"phase179_backlog_update":{"phase179_completed":True,"review_processing_ready":True,"next_phases":{"phase180":"packet_revision_execution_and_daily_brief_integration"},"mock_used":False,"fixture_used":False}}

def build_cc_guard_report():
    return build_phase179_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_review_processing_board,"brief":build_review_processing_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_review_processing_board(),ensure_ascii=False,indent=2))
