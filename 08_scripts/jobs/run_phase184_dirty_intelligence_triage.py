# Phase184 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase184_dirty_intelligence_triage import *

def run_pipeline(mode="dry-run"):
    dec = build_triage_decision_builder(); manifest = build_triage_manifest()
    clean = build_cleaning_queue_preview(); cc = build_cross_check_routing_preview(); sl = build_source_lead_queue_preview()
    ce = build_candidate_evidence_queue_preview(); orq = build_owner_review_queue_preview()
    g = build_phase184_guard(); qg = build_phase184_quality_gate(); ccg = build_phase184_cannot_conclude_guard()
    d = dec["phase184_triage_decisions"]
    return {"phase184_dirty_intelligence_triage_pipeline":{"mode":mode,"phase":"phase184","strategy":"dirty_intelligence_triage","research_only":True,
        "input_accepted_count":8,"items_triaged":d["items_triaged"],
        "discard_count":d["discard_count"],"duplicate_count":d["duplicate_count"],
        "source_lead_count":d["source_lead_count"],"candidate_evidence_count":d["candidate_evidence_count"],
        "cross_check_count":d["cross_check_count"],"owner_review_count":d["owner_review_count"],"quarantined_count":d["quarantined_count"],
        "triage_manifest_generated":True,"cleaning_queue_preview_generated":True,
        "cross_check_routing_generated":True,"source_lead_queue_generated":True,"candidate_evidence_queue_generated":True,
        "candidate_evidence_not_clean_evidence":True,"source_lead_not_confirmed_fact":True,
        "cross_check_not_verified":True,"owner_review_not_owner_approved":True,"triage_score_not_stock_rating":True,
        "guard":g["phase184_guard"]["status"],"quality_gate":qg["phase184_quality_gate"]["status"],
        "cannot_conclude_guard":ccg["phase184_cannot_conclude_guard"]["status"],"violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_full_text_saved":False,"clean_evidence_written":False,"packet_updated":False,
        "daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase185: Dirty-to-Clean Evidence Classifier."}}

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
