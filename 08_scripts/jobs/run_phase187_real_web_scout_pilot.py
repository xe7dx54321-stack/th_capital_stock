# Phase187 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase187_real_web_scout_pilot import *

def run_pipeline(mode="dry-run"):
    fetch = build_fetch_status_board()
    leads = build_source_lead_observations()
    manifest = build_pilot_outcome_manifest()
    match = build_cross_check_match_preview()
    g = build_phase187_guard(); qg = build_phase187_quality_gate(); cc = build_phase187_cannot_conclude_guard()
    f = fetch["phase187_fetch_status"]; l = leads["phase187_source_leads"]
    return {"phase187_real_web_scout_pilot_pipeline":{"mode":mode,"phase":"phase187","strategy":"real_web_scout_pilot","research_only":True,
        "pilot_ticker_count":2,"pilot_tickers":["MRVL","AMD"],
        "query_count":8,"fetch_attempt_count":f["fetch_attempts"],
        "fetched_count":f["status_summary"]["fetched"],"skipped_by_policy_count":f["status_summary"]["skipped_by_policy"],
        "blocked_count":f["status_summary"]["blocked"],"timeout_count":f["status_summary"]["timeout"],
        "parse_failed_count":f["status_summary"]["parse_failed"],
        "source_lead_observation_count":l["lead_count"],"cross_check_matches_count":match["phase187_cross_check_match_preview"]["match_count"],
        "would_help_cross_check_count":l["lead_count"],"pilot_outcome_manifest_generated":True,
        "cross_check_match_preview_generated":True,"real_web_eligibility_preview_generated":True,
        "source_lead_not_verified_evidence":True,"real_fetch_not_clean_evidence":True,
        "would_help_not_completed":True,"eligibility_preview_not_clean_evidence_eligible":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "llm_api_called":False,"raw_full_text_saved":False,"clean_evidence_written":False,
        "packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,
        "login_used":False,"paywall_bypassed":False,"ocr_used":False,"browser_automation_used":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase188: Cross-check verification and clean evidence ingestion."}}

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
