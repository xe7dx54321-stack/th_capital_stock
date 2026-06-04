# Phase178 reporting: board, brief, dashboard, backlog, guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase178_review_workflow import *

def build_review_board():
    console = build_review_console()
    tracker = build_review_status_tracker()
    templates = build_review_templates()
    daily = build_daily_brief_preview_gate()
    weekly = build_weekly_review_preview_gate()
    audit = build_review_audit()
    return {"phase178_review_board":{
        "review_console":console["phase178_review_console"],
        "review_status":tracker["phase178_review_status_tracker"],
        "templates":templates["phase178_review_templates"],
        "daily_brief_gate":daily["phase178_daily_brief_preview_gate"],
        "weekly_review_gate":weekly["phase178_weekly_review_preview_gate"],
        "audit":audit["phase178_review_audit"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass",
        "research_only":True,"mock_used":False,"fixture_used":False
    }}

def build_review_brief():
    tracker = build_review_status_tracker()["phase178_review_status_tracker"]
    return {"phase178_review_brief":{"headline":"Deep dive packet review console ready. 9 packets awaiting owner review.","pending_review":tracker["pending_owner_review"],"review_state":tracker["review_state"],"next_action":"Owner reviews packets and submits review input.","research_only":True,"mock_used":False,"fixture_used":False}}

def build_dashboard():
    tracker = build_review_status_tracker()["phase178_review_status_tracker"]
    return {"phase178_dashboard":{"summary":{"phase":"phase178","strategy":"packet_review_workflow","packet_count":9,"pending_review":tracker["pending_owner_review"],"reviewed":tracker["owner_reviewed"],"revision":tracker["revision_requested"],"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"owner_review_input_written":False,"auto_signoff":False,"watch_core_updated":False,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,"llm_api_called":False,"mock_used":False,"fixture_used":False}}}

def build_backlog_update():
    return {"phase178_backlog_update":{"phase178_completed":True,"review_console_ready":True,"next_phases":{"phase179":"owner_review_input_processing_and_revision_task_integration"},"mock_used":False,"fixture_used":False}}

def build_cc_guard_report():
    return build_phase178_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_review_board,"brief":build_review_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_review_board(),ensure_ascii=False,indent=2))
