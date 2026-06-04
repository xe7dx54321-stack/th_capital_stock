# Phase180 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase180_preview_waiting import *

def run_pipeline(mode="dry-run"):
    wl = build_owner_review_waiting_loop()
    digest = build_owner_action_digest()
    daily = build_daily_brief_packet_preview()
    weekly = build_weekly_review_packet_preview()
    brief_safe = build_brief_safe_summary()
    notification = build_notification_template()
    console = build_console_integration()
    g = build_phase180_guard(); qg = build_phase180_quality_gate(); cc = build_phase180_cannot_conclude_guard()

    w = wl["phase180_owner_review_waiting_loop"]; d = daily["phase180_daily_brief_packet_preview"]
    return {"phase180_brief_preview_pipeline":{
        "mode":mode,"phase":"phase180","strategy":"daily_weekly_brief_packet_integration_preview_and_owner_review_waiting_loop",
        "research_only":True,"packet_count":9,
        "owner_review_input_present":False,"review_input_state":w["review_input_state"],
        "pending_owner_review_count":w["pending_owner_review_count"],
        "owner_reviewed_count":w["owner_reviewed_count"],
        "daily_preview_gate_generated":daily["phase180_daily_brief_packet_preview"]["preview_gate_generated"],
        "weekly_preview_gate_generated":weekly["phase180_weekly_review_packet_preview"]["preview_gate_generated"],
        "daily_preview_allowed_count":d["daily_preview_allowed_count"],
        "weekly_preview_allowed_count":weekly["phase180_weekly_review_packet_preview"]["weekly_preview_allowed_count"],
        "blocked_pending_review_count":d["blocked_pending_review_count"],
        "owner_action_digest_generated":digest["phase180_owner_action_digest"]["digest_generated"],
        "brief_safe_summary_generated":True,
        "notification_template_generated":notification["phase180_notification_template"]["template_generated"],
        "notification_not_scheduler":notification["phase180_notification_template"]["template_not_scheduler_registration"],
        "console_integration_generated":True,
        "guard":g["phase180_guard"]["status"],"quality_gate":qg["phase180_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase180_cannot_conclude_guard"]["status"],"violations":qg["phase180_quality_gate"]["violations"],
        "auto_publish_daily_brief":False,"auto_publish_weekly_review":False,
        "owner_review_input_written":False,"auto_packet_signoff":False,"auto_revision_executed":False,
        "preview_not_trade_signal":True,"watch_core_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase181: Execute revision tasks and integrate approved packets into daily research brief."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
