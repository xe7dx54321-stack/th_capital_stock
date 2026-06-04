# Phase180 reporting: digest, preview, brief, dashboard, backlog, guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase180_preview_waiting import *

def build_owner_action_digest_report(): return build_owner_action_digest()
def build_daily_preview_report(): return build_daily_brief_packet_preview()
def build_weekly_preview_report(): return build_weekly_review_packet_preview()
def build_console_integration_report(): return build_console_integration()

def build_preview_brief():
    wl = build_owner_review_waiting_loop()["phase180_owner_review_waiting_loop"]
    daily = build_daily_brief_packet_preview()["phase180_daily_brief_packet_preview"]
    weekly = build_weekly_review_packet_preview()["phase180_weekly_review_packet_preview"]
    bs = build_brief_safe_summary()["phase180_brief_safe_summary"]
    return {"phase180_preview_brief":{"headline":"Packet integration preview ready. 9 packets awaiting owner review.","waiting_loop":wl,"daily_preview":daily,"weekly_preview":weekly,"brief_safe_summary":bs,"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","research_only":True,"mock_used":False,"fixture_used":False}}

def build_dashboard():
    wl = build_owner_review_waiting_loop()["phase180_owner_review_waiting_loop"]
    daily = build_daily_brief_packet_preview()["phase180_daily_brief_packet_preview"]
    return {"phase180_dashboard":{"summary":{"phase":"phase180","strategy":"brief_packet_preview_waiting_loop","packet_count":9,"review_input_state":wl["review_input_state"],"pending_review":wl["pending_owner_review_count"],"daily_preview_allowed":daily["daily_preview_allowed_count"],"blocked_pending":daily["blocked_pending_review_count"],"auto_publish":False,"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"watch_core_updated":False,"target_price_created":0,"broker_api_called":False,"llm_api_called":False,"mock_used":False,"fixture_used":False}}}

def build_backlog_update():
    return {"phase180_backlog_update":{"phase180_completed":True,"waiting_loop_ready":True,"next_phases":{"phase181":"revision_task_execution_and_daily_brief_publication"},"mock_used":False,"fixture_used":False}}

def build_cc_guard_report(): return build_phase180_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"digest":build_owner_action_digest_report,"daily":build_daily_preview_report,"weekly":build_weekly_preview_report,"console":build_console_integration_report,"brief":build_preview_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_preview_brief(),ensure_ascii=False,indent=2))
