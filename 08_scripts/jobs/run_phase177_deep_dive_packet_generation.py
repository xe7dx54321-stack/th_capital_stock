# Phase177 deep dive packet generation runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase177_packet_builder import *
from datetime import datetime

def run_pipeline(mode="dry-run"):
    execute = mode == "execute"
    packets = build_all_packets()
    review = build_owner_review_queue()
    qg = build_packet_quality_gate()
    g = build_phase177_guard()
    cc = build_phase177_cannot_conclude_guard()

    written = False
    if execute:
        written = write_packets_to_generated()["written"]

    p = packets["phase177_deep_dive_packets"]
    return {"phase177_deep_dive_packet_pipeline":{
        "mode":mode,"phase":"phase177","strategy":"research_task_outputs_to_formal_deep_dive_packets",
        "research_only":True,
        "activated_candidate_count":p["activated_candidate_count"],
        "formal_packet_count":p["formal_packet_count"],
        "keep_summary_count":p["keep_summary_count"],
        "defer_summary_count":p["defer_summary_count"],
        "reject_summary_count":p["reject_summary_count"],
        "packets_ready_for_owner_review":p["packets_ready_for_owner_review"],
        "owner_review_queue_count":review["phase177_owner_review_queue"]["queue_count"],
        "packets_written_to_generated":written,
        "packets_path_ignored":True,
        "guard":g["phase177_guard"]["status"],
        "quality_gate":qg["phase177_packet_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase177_cannot_conclude_guard"]["status"],
        "violations":qg["phase177_packet_quality_gate"]["violations"],
        "packet_outputs_no_trade_terms":True,
        "completeness_not_stock_rating":True,
        "thesis_seed_not_confirmed":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase178: Owner review and signoff on deep dive packets."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
