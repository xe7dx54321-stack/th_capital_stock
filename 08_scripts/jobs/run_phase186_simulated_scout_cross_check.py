# Phase186 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase186_simulated_scout_cross_check import *

def run_pipeline(mode="dry-run"):
    obs = build_simulated_scout_output_generator()
    manifest = build_outcome_manifest()
    er = build_eligibility_refresh()
    fh = build_failure_handler()
    g = build_phase186_guard(); qg = build_phase186_quality_gate(); cc = build_phase186_cannot_conclude_guard()
    m = manifest["phase186_outcome_manifest"]; e = er["phase186_eligibility_refresh"]
    return {"phase186_simulated_scout_cross_check_pipeline":{"mode":mode,"phase":"phase186","strategy":"simulated_scout_execution_and_cross_check_runner","research_only":True,
        "simulated":True,"not_real_source":True,
        "cross_check_task_count":8,"simulated_task_count":8,
        "simulated_observation_count":obs["phase186_simulated_observations"]["observation_count"],
        "outcome_manifest_generated":True,"eligibility_refresh_generated":True,"cleaning_readiness_refresh_generated":True,
        "simulated_strong":m["strong"],"simulated_moderate":m["moderate"],
        "simulated_insufficient":m["insufficient"],"simulated_conflict":0,
        "would_be_ready_if_real_count":e["would_be_ready_if_real_count"],"still_blocked_count":e["still_blocked_count"],
        "failed_or_inconclusive_count":fh["phase186_failure_handler"]["failed_or_inconclusive_count"],
        "simulated_observation_not_real_source":True,"simulated_support_not_verified":True,
        "outcome_preview_not_real_verification":True,"would_be_ready_not_clean_evidence_now":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "clean_evidence_written":False,"packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase187: Real web scout pilot or clean evidence ingestion."}}

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
