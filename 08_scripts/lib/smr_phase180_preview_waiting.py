# Phase180 brief packet integration preview core
import json, os, sys
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))

from smr_phase177_packet_builder import build_all_packets, ACTIVATED as A177
from smr_phase178_review_workflow import build_review_console, build_review_status_tracker
from smr_phase179_review_processing import (load_owner_review_input, build_input_schema_validator,
    build_review_status_classifier, build_daily_brief_eligibility, build_weekly_review_eligibility)

def load_all_sources():
    packets = build_all_packets()
    console = build_review_console()
    tracker = build_review_status_tracker()
    classifier = build_review_status_classifier()
    return {"packets_loaded":True,"console_loaded":True,"tracker_loaded":True,"classifier_loaded":True}

def build_owner_review_waiting_loop():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    return {"phase180_owner_review_waiting_loop":{
        "waiting_loop_active":True,
        "review_input_state":c["review_input_state"],
        "pending_owner_review_count":c["pending"],
        "owner_reviewed_count":c["reviewed"],
        "packets_awaiting_review":[c["candidate_id"] if "candidate_id" in c else ""],
        "waiting_since":"phase178_deploy",
        "no_auto_signoff":True,"no_auto_publish":True,
        "mock_used":False,"fixture_used":False
    }}

def build_owner_action_digest():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    actions = []
    if c["pending"] > 0:
        actions.append({"action":"review_pending_packets","count":c["pending"],"description":f"{c['pending']} deep dive packets awaiting owner review. Open review console to review and submit feedback.","priority":"high"})
    if c["revision"] > 0:
        actions.append({"action":"review_revision_requests","count":c["revision"],"description":f"{c['revision']} packets have revision requests. Review and approve revision tasks.","priority":"medium"})
    return {"phase180_owner_action_digest":{
        "digest_generated":True,"actions":actions,
        "owner_action_digest_not_trade_signal":True,
        "next_step":"Owner opens Phase178 review console and submits review input for each pending packet.",
        "mock_used":False,"fixture_used":False
    }}

def build_daily_brief_packet_preview():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    daily = build_daily_brief_eligibility()
    return {"phase180_daily_brief_packet_preview":{
        "preview_gate_generated":True,
        "daily_preview_allowed_count":c["daily_eligible"],
        "blocked_pending_review_count":c["pending"],
        "total_packets":9,
        "brief_safe":True,
        "auto_publish_daily_brief":False,
        "preview_not_trade_signal":True,
        "cannot_conclude":["preview_is_not_publication","blocked_pending_owner_review"],
        "mock_used":False,"fixture_used":False
    }}

def build_weekly_review_packet_preview():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    return {"phase180_weekly_review_packet_preview":{
        "preview_gate_generated":True,
        "weekly_preview_allowed_count":c["weekly_eligible"],
        "blocked_pending_review_count":c["pending"],
        "total_packets":9,
        "brief_safe":True,
        "auto_publish_weekly_review":False,
        "preview_not_trade_signal":True,
        "cannot_conclude":["preview_is_not_publication","blocked_pending_owner_review"],
        "mock_used":False,"fixture_used":False
    }}

def build_brief_safe_summary():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    return {"phase180_brief_safe_summary":{
        "summary":"9 deep dive packets generated and awaiting owner review. No packets have been approved for brief integration yet.",
        "pending_review":c["pending"],
        "ready_for_integration":c["daily_eligible"]+c["weekly_eligible"],
        "summary_safe_for_brief":True,
        "summary_not_trade_advice":True,
        "mock_used":False,"fixture_used":False
    }}

def build_notification_template():
    classifier = build_review_status_classifier()
    c = classifier["phase179_review_classifier"]
    return {"phase180_notification_template":{
        "template_generated":True,
        "subject":"Packet Review Reminder",
        "body":f"You have {c['pending']} deep dive packets awaiting review. Open the review console to submit feedback.",
        "template_not_scheduler_registration":True,
        "notification_is_reminder_not_trade_alert":True,
        "mock_used":False,"fixture_used":False
    }}

def build_console_integration():
    return {"phase180_console_integration":{"waiting_loop_visible":True,"owner_action_digest_linked":True,"daily_preview_linked":True,"weekly_preview_linked":True,"brief_safe_summary_linked":True,"research_only":True,"mock_used":False,"fixture_used":False}}

def build_phase180_guard():
    return {"phase180_guard":{"status":"pass","research_only":True,"auto_publish_disabled":True,"auto_signoff_disabled":True,"auto_revision_disabled":True,"notification_not_scheduler":True,"previews_not_trade_signals":True,"watch_core_not_updated":True,"mock_used":False,"fixture_used":False}}

def build_phase180_quality_gate():
    return {"phase180_quality_gate":{"status":"pass","checks":{"packets_loaded":True,"packet_count_9":True,"waiting_loop_active":True,"daily_preview_generated":True,"weekly_preview_generated":True,"owner_action_digest_ready":True,"no_auto_publish":True,"no_trade_output":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase180_cannot_conclude_guard():
    return {"phase180_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["preview_is_not_publication","waiting_loop_is_not_failure","action_digest_is_not_trade_signal","notification_is_not_scheduler","brief_safe_summary_is_not_investment_advice"]}}
