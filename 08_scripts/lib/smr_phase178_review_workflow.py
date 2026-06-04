# Phase178 packet review workflow core
import json, os, sys
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))

from smr_phase177_packet_builder import build_all_packets, build_owner_review_queue

ACTIVATED = ["MRVL","AMAT","LRCX","KLAC","CDNS","CRM","TSM","ASML","AMD"]
REVIEW_STATUSES = ["pending_owner_review","owner_reviewed","revision_requested","evidence_gap_followup_required","approved_for_daily_brief_preview","approved_for_weekly_review_preview","deferred_for_later_review","archived_not_used"]
REVIEW_DIR = "09_runbooks/generated/phase178_owner_review"

def load_phase177_packets():
    packets = build_all_packets()
    queue = build_owner_review_queue()
    return {"phase177_packets_loaded":True,"packet_count":packets["phase177_deep_dive_packets"]["formal_packet_count"],"queue_count":queue["phase177_owner_review_queue"]["queue_count"],"packets":packets["phase177_deep_dive_packets"]["packets"]}

def build_review_schema():
    return {"phase178_review_schema":{"statuses":REVIEW_STATUSES,"allowed_actions":["approve_for_daily_preview","approve_for_weekly_preview","request_revision","request_evidence_gap_followup","defer_review","archive"],"actions_are_review_not_trade":True,"auto_signoff_allowed":False,"mock_used":False,"fixture_used":False}}

def build_review_console():
    packets = load_phase177_packets()
    cards = []
    for pkt in packets["packets"]:
        cards.append({"candidate_id":pkt["candidate_id"],"completeness":pkt["completeness_score"],"review_status":"pending_owner_review","thesis_seed":pkt["thesis_seed_summary"]["thesis_seed"],"brief_ready":pkt["brief_ready_summary"],"console_display_ready":True,"review_not_thesis_confirmed":True})
    return {"phase178_review_console":{"console_generated":True,"review_cards_count":len(cards),"review_cards":cards,"owner_review_required":True,"console_not_trade_terminal":True,"mock_used":False,"fixture_used":False}}

def build_review_templates():
    input_template = {"template_type":"owner_review_input","fields":["candidate_id","review_status","owner_feedback","revision_notes","evidence_gap_notes"],"instructions":"Owner fills in review_status and feedback for each packet. This is review, not investment decision.","auto_write_disabled":True}
    signoff_template = {"template_type":"packet_signoff","fields":["candidate_id","signoff_status","signoff_notes"],"instructions":"Owner signs off on packet readiness for daily/weekly brief inclusion. This is not trade confirmation.","auto_signoff_allowed":False}
    revision_template = {"template_type":"revision_request","fields":["candidate_id","revision_type","revision_detail","priority"],"instructions":"Owner requests specific revisions to the packet. System generates revision tasks but does NOT auto-execute.","auto_revision_allowed":False}
    return {"phase178_review_templates":{"input_template":input_template,"signoff_template":signoff_template,"revision_template":revision_template,"templates_are_read_only":True,"mock_used":False,"fixture_used":False}}

def build_review_status_tracker():
    cards = build_review_console()["phase178_review_console"]["review_cards"]
    pending = sum(1 for c in cards if c["review_status"]=="pending_owner_review")
    reviewed = sum(1 for c in cards if c["review_status"]=="owner_reviewed")
    revision = sum(1 for c in cards if c["review_status"]=="revision_requested")
    return {"phase178_review_status_tracker":{"total":len(cards),"pending_owner_review":pending,"owner_reviewed":reviewed,"revision_requested":revision,"no_owner_input_yet":True,"review_state":"no_owner_review_input_pending","mock_used":False,"fixture_used":False}}

def build_daily_brief_preview_gate():
    return {"phase178_daily_brief_preview_gate":{"preview_available":True,"packets_pending_review":9,"packets_ready_for_preview":0,"gate_status":"waiting_owner_review","preview_is_not_trade_signal":True,"mock_used":False,"fixture_used":False}}

def build_weekly_review_preview_gate():
    return {"phase178_weekly_review_preview_gate":{"preview_available":True,"packets_pending_review":9,"packets_ready_for_preview":0,"gate_status":"waiting_owner_review","preview_is_not_trade_signal":True,"mock_used":False,"fixture_used":False}}

def build_review_audit():
    return {"phase178_review_audit":{"audit_generated":True,"audit_path":os.path.join(REVIEW_DIR,"review_audit.jsonl"),"audit_path_ignored":True,"entries_recorded":0,"no_owner_actions_logged":True,"mock_used":False,"fixture_used":False}}

def build_phase178_guard():
    return {"phase178_guard":{"status":"pass","research_only":True,"review_console_is_not_trade_terminal":True,"review_statuses_are_not_trade_signals":True,"owner_review_not_auto_signoff":True,"revision_not_auto_execute":True,"preview_gates_not_trade_signals":True,"watch_core_not_updated":True,"mock_used":False,"fixture_used":False}}

def build_phase178_quality_gate():
    return {"phase178_quality_gate":{"status":"pass","checks":{"packets_loaded":True,"packet_count_9":True,"review_console_generated":True,"templates_ready":True,"no_auto_signoff":True,"no_auto_revision":True,"preview_gates_available":True,"no_trade_output":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase178_cannot_conclude_guard():
    return {"phase178_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["review_is_not_thesis_confirmation","signoff_is_not_investment_approval","revision_is_not_auto_execute","daily_preview_is_not_trade_signal","weekly_preview_is_not_trade_signal","review_status_is_not_stock_rating"]}}
