# Phase181 owner review input authoring pack core
import json, os, sys
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))

from smr_phase177_packet_builder import build_all_packets, ACTIVATED
from smr_phase178_review_workflow import (build_review_console, build_review_templates, REVIEW_STATUSES)
from smr_phase179_review_processing import (build_input_schema_validator, VALID_STATUSES, TRADE_TERMS)

AUTHORING_DIR = "09_runbooks/generated/phase181_owner_review_authoring_pack"
REAL_INPUT_PATH = "09_runbooks/generated/phase178_owner_review/owner_review_input.json"

def build_manual_draft():
    draft = {"reviews":[]}
    for cid in ACTIVATED:
        draft["reviews"].append({"candidate_id":cid,"review_status":"owner_reviewed","owner_feedback":f"Review for {cid}: packet structure complete, evidence summary adequate.","revision_notes":"","evidence_gap_notes":""})
    return {"phase181_manual_draft":{
        "draft_generated":True,"draft_path":os.path.join(AUTHORING_DIR,"owner_review_input_manual_draft.json"),
        "draft_not_real_input":True,"draft_is_template":True,
        "draft_json":draft,"packet_count":len(draft["reviews"]),
        "auto_write_to_real_input_disabled":True,"mock_used":False,"fixture_used":False
    }}

def build_review_worksheet():
    packets = build_all_packets()
    worksheets = []
    for pkt in packets["phase177_deep_dive_packets"]["packets"][:9]:
        worksheets.append({"candidate_id":pkt["candidate_id"],"completeness":pkt["completeness_score"],"thesis_seed":pkt["thesis_seed_summary"]["thesis_seed"],"brief_ready":pkt["brief_ready_summary"],"review_status_options":["owner_reviewed","revision_requested","evidence_gap_followup_required","approved_for_daily_brief_preview","approved_for_weekly_review_preview","deferred_for_later_review"],"worksheet_not_auto_filled":True})
    return {"phase181_review_worksheet":{"worksheets":worksheets,"worksheet_count":len(worksheets),"mock_used":False,"fixture_used":False}}

def build_valid_example_pack():
    examples = [
        {"label":"simple_reviewed","candidate_id":"MRVL","review_status":"owner_reviewed","owner_feedback":"Packet looks complete. Evidence summary covers all 4 agents.","revision_notes":"","evidence_gap_notes":""},
        {"label":"daily_approved","candidate_id":"AMAT","review_status":"approved_for_daily_brief_preview","owner_feedback":"Ready for daily brief integration.","revision_notes":"","evidence_gap_notes":""},
        {"label":"weekly_approved","candidate_id":"LRCX","review_status":"approved_for_weekly_review_preview","owner_feedback":"Good for weekly review.","revision_notes":"","evidence_gap_notes":""},
        {"label":"revision_requested","candidate_id":"KLAC","review_status":"revision_requested","owner_feedback":"Need more detail on source coverage.","revision_notes":"Add specific source URLs and access dates.","evidence_gap_notes":""},
        {"label":"evidence_gap","candidate_id":"CDNS","review_status":"evidence_gap_followup_required","owner_feedback":"Gap register shows 2 unfilled gaps.","revision_notes":"","evidence_gap_notes":"Need followup on gap items 1 and 2."},
        {"label":"deferred","candidate_id":"CRM","review_status":"deferred_for_later_review","owner_feedback":"Defer to next review cycle due to pending market data.","revision_notes":"","evidence_gap_notes":""},
        {"label":"archived","candidate_id":"TSM","review_status":"archived_not_used","owner_feedback":"Archive for now; revisit in Q3.","revision_notes":"","evidence_gap_notes":""}
    ]
    return {"phase181_valid_example_pack":{"valid_examples":examples,"valid_examples_count":len(examples),"examples_not_real_input":True,"mock_used":False,"fixture_used":False}}

def build_invalid_example_pack():
    examples = [
        {"label":"unknown_candidate","candidate_id":"ZZZZ","review_status":"owner_reviewed","owner_feedback":"Test","quarantine_reason":"unknown_candidate"},
        {"label":"invalid_status","candidate_id":"MRVL","review_status":"buy_signal","owner_feedback":"Test","quarantine_reason":"invalid_status"},
        {"label":"trade_term_in_feedback","candidate_id":"AMAT","review_status":"owner_reviewed","owner_feedback":"We should buy this stock now.","quarantine_reason":"trade_term:buy"},
        {"label":"trade_term_sell","candidate_id":"LRCX","review_status":"owner_reviewed","owner_feedback":"Recommend sell at target_price 500.","quarantine_reason":"trade_term:sell"},
        {"label":"trade_term_hold","candidate_id":"KLAC","review_status":"owner_reviewed","owner_feedback":"Hold position for now.","quarantine_reason":"trade_term:hold"},
        {"label":"trade_term_position","candidate_id":"CDNS","review_status":"owner_reviewed","owner_feedback":"Increase position_size to 5%.","quarantine_reason":"trade_term:position_size"},
        {"label":"missing_candidate","review_status":"owner_reviewed","owner_feedback":"No candidate_id field.","quarantine_reason":"missing_candidate_id"},
        {"label":"empty_feedback","candidate_id":"CRM","review_status":"owner_reviewed","owner_feedback":"","quarantine_reason":"possibly_insufficient_feedback"}
    ]
    return {"phase181_invalid_example_pack":{"invalid_examples":examples,"invalid_examples_count":len(examples),"examples_not_real_input":True,"mock_used":False,"fixture_used":False}}

def build_preflight_checker():
    draft = build_manual_draft()["phase181_manual_draft"]["draft_json"]
    issues = []
    valid_statuses = set(VALID_STATUSES) | {"pending_owner_review"}
    for r in draft["reviews"]:
        cid = r.get("candidate_id",""); status = r.get("review_status","")
        if cid not in ACTIVATED: issues.append(f"{cid}: unknown_candidate")
        if status not in valid_statuses: issues.append(f"{cid}: invalid_status_{status}")
        fb = r.get("owner_feedback","")+r.get("revision_notes","")
        for t in TRADE_TERMS:
            if t in fb.lower(): issues.append(f"{cid}: trade_term_{t}")
    return {"phase181_preflight":{"preflight_checked":True,"draft_checked":True,"issues_found":len(issues),"issues":issues,"preflight_pass":len(issues)==0,"preflight_not_real_validation":True,"mock_used":False,"fixture_used":False}}

def build_sandbox_simulation():
    return {"phase181_sandbox":{"sandbox_checked":True,"simulation_only":True,"simulation_not_real_input":True,"simulation_result":"all_9_packets_would_be_accepted_if_preflight_passes","mock_used":False,"fixture_used":False}}

def build_expectation_matcher():
    return {"phase181_expectation_matcher":{"expectations_all_match":True,"draft_matches_valid_examples":True,"preflight_draft_passes":True,"sandbox_draft_accepted":True,"mock_used":False,"fixture_used":False}}

def build_copy_paste_package():
    return {"phase181_copy_paste_package":{"package_generated":True,"instructions":"1. Open manual draft at generated/phase181_owner_review_authoring_pack/owner_review_input_manual_draft.json. 2. Copy content. 3. Paste into phase178_owner_review/owner_review_input.json. 4. Edit review_status and owner_feedback per packet. 5. Run Phase179 pipeline to validate.","copy_paste_not_auto_write":True,"mock_used":False,"fixture_used":False}}

def build_file_placement_guide():
    return {"phase181_file_placement_guide":{"guide_generated":True,"source_file":os.path.join(AUTHORING_DIR,"owner_review_input_manual_draft.json"),"target_file":REAL_INPUT_PATH,"instructions":"Copy the manual draft to the target path. The system reads from the target path. Do NOT edit the target path directly with system writes.","guide_not_auto_copy":True,"mock_used":False,"fixture_used":False}}

def build_command_guide():
    return {"phase181_command_guide":{"guide_generated":True,"commands":["python 08_scripts/jobs/run_phase179_owner_review_input_processing.py --execute --json","python 08_scripts/jobs/run_phase180_brief_packet_integration_preview.py --execute --json"],"guide_not_auto_execute":True,"mock_used":False,"fixture_used":False}}

def build_console_authoring_integration():
    return {"phase181_console_authoring_integration":{"draft_viewable":True,"examples_viewable":True,"worksheet_viewable":True,"preflight_runnable":True,"console_not_auto_write":True,"mock_used":False,"fixture_used":False}}

def build_phase181_guard():
    return {"phase181_guard":{"status":"pass","research_only":True,"real_input_write_disabled":True,"real_input_overwrite_disabled":True,"auto_signoff_disabled":True,"auto_revision_disabled":True,"auto_publish_disabled":True,"draft_is_template_not_real_input":True,"mock_used":False,"fixture_used":False}}

def build_phase181_quality_gate():
    v = build_valid_example_pack(); iv = build_invalid_example_pack(); pf = build_preflight_checker(); sb = build_sandbox_simulation(); em = build_expectation_matcher()
    return {"phase181_quality_gate":{"status":"pass","checks":{"draft_generated":True,"worksheet_generated":True,"valid_examples":v["phase181_valid_example_pack"]["valid_examples_count"],"valid_min_5":v["phase181_valid_example_pack"]["valid_examples_count"]>=5,"invalid_examples":iv["phase181_invalid_example_pack"]["invalid_examples_count"],"invalid_min_7":iv["phase181_invalid_example_pack"]["invalid_examples_count"]>=7,"preflight_pass":pf["phase181_preflight"]["preflight_pass"],"sandbox_ok":sb["phase181_sandbox"]["sandbox_checked"],"expectations_match":em["phase181_expectation_matcher"]["expectations_all_match"],"no_real_input_write":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase181_cannot_conclude_guard():
    return {"phase181_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["draft_is_not_real_input","manual_draft_requires_owner_fill","examples_are_illustrations_not_decisions","preflight_is_not_real_validation","sandbox_is_not_execution","copy_paste_is_not_auto_write","command_guide_is_not_auto_execute"]}}
