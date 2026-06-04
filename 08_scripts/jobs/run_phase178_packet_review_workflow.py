# Phase178 packet review workflow runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase178_review_workflow import *

def run_pipeline(mode="dry-run"):
    console = build_review_console()
    tracker = build_review_status_tracker()
    templates = build_review_templates()
    daily = build_daily_brief_preview_gate()
    weekly = build_weekly_review_preview_gate()
    audit = build_review_audit()
    g = build_phase178_guard(); qg = build_phase178_quality_gate(); cc = build_phase178_cannot_conclude_guard()

    t = tracker["phase178_review_status_tracker"]
    return {"phase178_packet_review_pipeline":{
        "mode":mode,"phase":"phase178","strategy":"deep_dive_packet_console_and_owner_review_workflow",
        "research_only":True,
        "packet_count":9,"review_queue_count":9,
        "review_console_generated":True,"review_cards_generated":True,
        "review_templates_generated":True,
        "owner_review_input_present":False,"review_state":t["review_state"],
        "pending_owner_review_count":t["pending_owner_review"],
        "owner_reviewed_count":t["owner_reviewed"],
        "revision_requested_count":t["revision_requested"],
        "daily_brief_preview_gate":daily["phase178_daily_brief_preview_gate"]["gate_status"],
        "weekly_review_preview_gate":weekly["phase178_weekly_review_preview_gate"]["gate_status"],
        "audit_generated":audit["phase178_review_audit"]["audit_generated"],
        "guard":g["phase178_guard"]["status"],
        "quality_gate":qg["phase178_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase178_cannot_conclude_guard"]["status"],
        "violations":qg["phase178_quality_gate"]["violations"],
        "owner_review_input_written":False,"auto_packet_signoff":False,"auto_revision_executed":False,
        "review_not_thesis_confirmed":True,"daily_preview_not_trade_signal":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase179: Process owner review input and generate revision tasks."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
