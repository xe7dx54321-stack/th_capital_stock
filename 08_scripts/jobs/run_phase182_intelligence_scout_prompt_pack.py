# Phase182 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase182_intelligence_scout_prompt_pack import *

def run_pipeline(mode="dry-run"):
    uni = build_activated_candidate_scout_universe()
    tax = build_scout_prompt_taxonomy()
    cards = build_scout_prompt_cards()
    plans = build_ticker_specific_prompt_plan()
    src = build_source_category_map()
    schema = build_dirty_intelligence_item_schema()
    contract = build_scout_output_contract()
    smeta = build_source_metadata_requirements()
    safety = build_prompt_safety_rules()
    cc = build_prompt_cannot_conclude_rules()
    sched = build_prompt_scheduling_policy()
    prio = build_prompt_priority_policy()
    exp = build_expected_output_examples()
    inv = build_invalid_output_examples()
    inbox = build_dirty_inbox_interface_preview()
    ci = build_console_integration()
    g = build_phase182_guard()
    qg = build_phase182_quality_gate()
    ccg = build_phase182_cannot_conclude_guard()

    return {"phase182_intelligence_scout_prompt_pack_pipeline":{
        "mode":mode,"phase":"phase182","strategy":"intelligence_scout_prompt_pack","research_only":True,
        "activated_candidate_count":uni["phase182_scout_universe"]["activated_candidate_count"],
        "prompt_type_count":tax["phase182_prompt_taxonomy"]["prompt_type_count"],
        "prompt_card_count":cards["phase182_prompt_cards"]["prompt_card_count"],
        "ticker_scout_plan_count":plans["phase182_ticker_scout_plan"]["ticker_scout_plan_count"],
        "source_category_count":src["phase182_source_category_map"]["source_category_count"],
        "dirty_item_schema_defined":True,"output_contract_defined":True,
        "source_metadata_defined":True,"safety_rules_count":safety["phase182_prompt_safety_rules"]["safety_rule_count"],
        "cc_rules_count":cc["phase182_prompt_cc_rules"]["rule_count"],
        "scheduling_policy_defined":True,"priority_policy_defined":True,
        "expected_output_examples":exp["phase182_expected_output_examples"]["example_count"],
        "invalid_output_examples":inv["phase182_invalid_output_examples"]["invalid_example_count"],
        "dirty_inbox_preview_defined":True,"console_integration_defined":True,
        "guard":g["phase182_guard"]["status"],"quality_gate":qg["phase182_quality_gate"]["status"],
        "cannot_conclude_guard":ccg["phase182_cannot_conclude_guard"]["status"],"violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_saved":False,"clean_evidence_written":False,"packet_updated":False,
        "daily_brief_updated":False,"weekly_review_updated":False,
        "auto_dispatch_disabled":True,"scheduler_registration_disabled":True,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase183: Dirty Intelligence Inbox ingestion pipeline."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
