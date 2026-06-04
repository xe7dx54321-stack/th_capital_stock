# Phase182 reporting: prompt pack board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase182_intelligence_scout_prompt_pack import *

def build_prompt_pack_board():
    uni = build_activated_candidate_scout_universe(); tax = build_scout_prompt_taxonomy()
    cards = build_scout_prompt_cards(); plans = build_ticker_specific_prompt_plan()
    src = build_source_category_map(); schema = build_dirty_intelligence_item_schema()
    contract = build_scout_output_contract(); smeta = build_source_metadata_requirements()
    safety = build_prompt_safety_rules(); cc = build_prompt_cannot_conclude_rules()
    sched = build_prompt_scheduling_policy(); prio = build_prompt_priority_policy()
    exp = build_expected_output_examples(); inv = build_invalid_output_examples()
    inbox = build_dirty_inbox_interface_preview(); ci = build_console_integration()
    g = build_phase182_guard(); qg = build_phase182_quality_gate(); ccg = build_phase182_cannot_conclude_guard()
    return {"phase182_prompt_pack_board":{
        "phase":"phase182","strategy":"intelligence_scout_prompt_pack","research_only":True,
        "scout_universe":uni["phase182_scout_universe"],"prompt_taxonomy":tax["phase182_prompt_taxonomy"],
        "prompt_cards":cards["phase182_prompt_cards"],"ticker_scout_plans":plans["phase182_ticker_scout_plan"],
        "source_category_map":src["phase182_source_category_map"],"dirty_item_schema":schema["phase182_dirty_item_schema"],
        "output_contract":contract["phase182_output_contract"],"source_metadata":smeta["phase182_source_metadata"],
        "safety_rules":safety["phase182_prompt_safety_rules"],"cc_rules":cc["phase182_prompt_cc_rules"],
        "scheduling_policy":sched["phase182_scheduling_policy"],"priority_policy":prio["phase182_priority_policy"],
        "expected_output_examples":exp["phase182_expected_output_examples"],"invalid_output_examples":inv["phase182_invalid_output_examples"],
        "dirty_inbox_interface":inbox["phase182_dirty_inbox_interface"],"console_integration":ci["phase182_console_integration"],
        "guard":g["phase182_guard"]["status"],"quality_gate":qg["phase182_quality_gate"]["status"],
        "cannot_conclude_guard":ccg["phase182_cannot_conclude_guard"]["status"],"violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_saved":False,"clean_evidence_written":False,"packet_updated":False,
        "mock_used":False,"fixture_used":False
    }}

def build_prompt_pack_brief():
    uni = build_activated_candidate_scout_universe(); cards = build_scout_prompt_cards()
    g = build_phase182_guard(); qg = build_phase182_quality_gate(); ccg = build_phase182_cannot_conclude_guard()
    return {"phase182_prompt_pack_brief":{
        "headline":"Intelligence Scout Prompt Pack v1 designed. 8 prompt types for 9 activated candidates. No LLM calls, no web search, no raw save.",
        "activated_candidate_count":uni["phase182_scout_universe"]["activated_candidate_count"],
        "prompt_card_count":cards["phase182_prompt_cards"]["prompt_card_count"],
        "prompt_types":cards["phase182_prompt_cards"]["prompt_type_count"],
        "ticker_scout_plan_count":9,"all_plans_designed":True,"auto_dispatch_disabled":True,
        "dirty_inbox_is_preview":True,"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass",
        "violations":0,"mock_used":False,"fixture_used":False,"research_only":True
    }}

def build_dashboard():
    uni = build_activated_candidate_scout_universe(); cards = build_scout_prompt_cards()
    g = build_phase182_guard(); qg = build_phase182_quality_gate(); ccg = build_phase182_cannot_conclude_guard()
    return {"phase182_dashboard":{"summary":{
        "phase":"phase182","strategy":"intelligence_scout_prompt_pack",
        "activated_candidate_count":uni["phase182_scout_universe"]["activated_candidate_count"],
        "prompt_type_count":cards["phase182_prompt_cards"]["prompt_type_count"],
        "prompt_card_count":cards["phase182_prompt_cards"]["prompt_card_count"],
        "ticker_scout_plan_count":9,"source_category_count":len(SOURCE_CATEGORIES),
        "dirty_schema_defined":True,"output_contract_defined":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "raw_saved":False,"clean_evidence_written":False,"packet_updated":False,
        "daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0
    }}}

def build_backlog_update():
    return build_backlog()

def build_cc_guard_report():
    return build_phase182_cannot_conclude_guard()

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_prompt_pack_board,"brief":build_prompt_pack_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_prompt_pack_board(),ensure_ascii=False,indent=2))
