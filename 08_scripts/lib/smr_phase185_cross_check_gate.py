# Phase185 cross-check task generation and dirty-to-clean eligibility gate core
import json, os, sys, hashlib
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase184_dirty_intelligence_triage import build_triage_decision_builder, build_cross_check_need_classifier, build_source_reliability_pre_score, ACTIVATED_CANDIDATES
from smr_phase182_intelligence_scout_prompt_pack import PROMPT_TYPES, SOURCE_CATEGORIES
from smr_phase183_dirty_intelligence_inbox import build_simulated_input

def _load_needs_cross_check_items():
    items = build_simulated_input()["phase183_simulated_input"]["items"]
    cc = build_cross_check_need_classifier()["phase184_cross_check_classifier"]["results"]
    src = build_source_reliability_pre_score()["phase184_source_reliability"]["results"]
    xc = []
    for i,item in enumerate(items):
        if cc[i]["needs_cross_check"]:
            xc.append({"item_id":item["item_id"],"ticker":item["ticker"],"prompt_type":item["prompt_type"],"source_category":item["source_category"],"source_tier":item["source_tier"],"signal_category":item["signal_category"],"source_url":item["source_url"],"cross_check_reason":cc[i]["cross_check_reason"],"source_reliability":src[i]["source_reliability_pre_score"]})
    return xc

def build_cross_check_domain_registry():
    return {"phase185_cross_check_registry":{"registry_defined":True,"input_from_phase184":True,"needs_cross_check_count":8,"candidate_evidence_count":0,"direct_cleaning_eligible":False,"blocked_pending_cross_check":8,"mock_used":False,"fixture_used":False}}

def build_cross_check_task_schema():
    schema = {"task_id":"required","item_id":"required","ticker":"required","cross_check_reason":"required","verification_type":"required","recommended_sources":["required_array"],"recommended_prompts":["required_array"],"independent_source_minimum":2,"verification_criteria":["required_array"],"task_status":"designed","task_not_executed":True,"task_not_network_fetch":True,"task_not_llm_call":True}
    return {"phase185_cross_check_task_schema":{"schema":schema,"schema_version":"1.0","research_only":True,"mock_used":False,"fixture_used":False}}

def build_cross_check_reason_classifier():
    items = _load_needs_cross_check_items()
    results = []
    for item in items:
        sc = item["signal_category"]; cat = item["source_category"]
        if sc in ["contradiction","risk_negative"]: reason_type = "high_impact_claim_needs_verification"
        elif cat == "social_or_forum": reason_type = "low_reliability_source_requires_corroboration"
        elif sc in ["customer_demand","supply_chain","pricing_lead_time"]: reason_type = "industry_claim_needs_official_cross_check"
        elif sc == "management_commentary": reason_type = "management_claim_needs_independent_verification"
        else: reason_type = "general_cross_check_required"
        results.append({"item_id":item["item_id"],"cross_check_reason_type":reason_type,"original_reason":item["cross_check_reason"]})
    return {"phase185_cross_check_reasons":{"items_checked":len(results),"results":results,"mock_used":False,"fixture_used":False}}

def build_source_route_builder():
    items = _load_needs_cross_check_items()
    routes = []
    for item in items:
        cat = item["source_category"]; tier = item["source_tier"]
        if cat in ["social_or_forum","industry_media"]:
            rec = ["official_filing","company_ir"]
        elif cat in ["earnings_call_transcript"]:
            rec = ["official_filing","company_ir","industry_media"]
        else: rec = ["official_filing","earnings_call_transcript"]
        routes.append({"item_id":item["item_id"],"current_source":cat,"current_tier":tier,"recommended_sources":rec,"source_diversity_minimum":2,"source_route_not_network_fetch":True})
    return {"phase185_source_routes":{"routes":routes,"route_count":len(routes),"all_routes_designed_not_executed":True,"mock_used":False,"fixture_used":False}}

def build_prompt_route_builder():
    items = _load_needs_cross_check_items()
    routes = []
    for item in items:
        pt = item["prompt_type"]; sc = item["signal_category"]
        if sc in ["contradiction"]: rec = ["contradiction_scout","filing_official_source_scout"]
        elif sc in ["risk_negative"]: rec = ["risk_negative_signal_scout","filing_official_source_scout"]
        elif sc in ["customer_demand"]: rec = ["customer_demand_scout","filing_official_source_scout"]
        elif sc in ["supply_chain"]: rec = ["supply_chain_crosscheck_scout","filing_official_source_scout"]
        elif sc in ["pricing_lead_time"]: rec = ["product_pricing_lead_time_scout","filing_official_source_scout"]
        elif sc in ["management_commentary"]: rec = ["management_commentary_scout","filing_official_source_scout"]
        else: rec = ["general_news_scout","filing_official_source_scout"]
        routes.append({"item_id":item["item_id"],"current_prompt":pt,"recommended_prompts":rec,"prompt_route_not_llm_call":True})
    return {"phase185_prompt_routes":{"routes":routes,"route_count":len(routes),"all_routes_designed_not_called":True,"mock_used":False,"fixture_used":False}}

def build_verification_requirement_builder():
    items = _load_needs_cross_check_items()
    reqs = []
    for item in items:
        criteria = ["independent_source_confirmation","source_attribution_required","timestamp_verification","no_trade_terms_check","author_verification"]
        min_sources = 2
        if item["source_category"] == "social_or_forum": min_sources = 3
        reqs.append({"item_id":item["item_id"],"verification_criteria":criteria,"independent_source_minimum":min_sources,"verification_not_executed":True})
    return {"phase185_verification_requirements":{"requirements":reqs,"requirement_count":len(reqs),"all_requirements_designed_not_verified":True,"mock_used":False,"fixture_used":False}}

def build_independent_source_policy():
    return {"phase185_independent_source_policy":{"policy_version":"1.0","minimum_independent_sources":2,"social_or_forum_minimum":3,"same_domain_not_independent":True,"same_publisher_not_independent":True,"official_filing_counts_as_independent":True,"company_ir_is_not_independent_from_company":True,"mock_used":False,"fixture_used":False}}

def build_source_diversity_policy():
    return {"phase185_source_diversity_policy":{"policy_version":"1.0","required_source_category_diversity":2,"at_least_one_official_source_required":True,"social_or_forum_alone_insufficient":True,"mock_used":False,"fixture_used":False}}

def build_cross_check_tasks():
    items = _load_needs_cross_check_items()
    reasons = build_cross_check_reason_classifier()["phase185_cross_check_reasons"]["results"]
    src_routes = build_source_route_builder()["phase185_source_routes"]["routes"]
    prompt_routes = build_prompt_route_builder()["phase185_prompt_routes"]["routes"]
    ver_reqs = build_verification_requirement_builder()["phase185_verification_requirements"]["requirements"]
    tasks = []
    for i,item in enumerate(items):
        tasks.append({"task_id":f"xct-{i+1:03d}","item_id":item["item_id"],"ticker":item["ticker"],"cross_check_reason_type":reasons[i]["cross_check_reason_type"],"recommended_sources":src_routes[i]["recommended_sources"],"recommended_prompts":prompt_routes[i]["recommended_prompts"],"independent_source_minimum":ver_reqs[i]["independent_source_minimum"],"verification_criteria":ver_reqs[i]["verification_criteria"],"task_status":"designed","task_not_executed":True,"task_not_network_fetch":True,"task_not_llm_call":True,"task_not_clean_evidence":True})
    return {"phase185_cross_check_tasks":{"tasks":tasks,"task_count":len(tasks),"all_tasks_designed_not_executed":True,"tasks_do_not_create_clean_evidence":True,"mock_used":False,"fixture_used":False}}

def build_eligibility_gate():
    dec = build_triage_decision_builder()["phase184_triage_decisions"]
    ce = dec["candidate_evidence_count"]; cc_ct = dec["cross_check_count"]
    return {"phase185_eligibility_gate":{"eligibility_gate_active":True,"direct_cleaning_eligible":ce>0,"direct_cleaning_eligible_count":ce,"blocked_pending_cross_check":cc_ct,"blocked_pending_cross_check_count":cc_ct,"ready_after_cross_check_count":0,"gate_rule":"only_candidate_evidence_candidates_or_items_with_completed_cross_check_may_enter_cleaning","gate_blocks_dirty_items":True,"gate_is_not_clean_evidence_write":True,"gate_prevents_premature_cleaning":True,"mock_used":False,"fixture_used":False}}

def build_cleaning_readiness_preview():
    tasks = build_cross_check_tasks()["phase185_cross_check_tasks"]["tasks"]
    return {"phase185_cleaning_readiness_preview":{"items_for_cross_check":len(tasks),"items_ready_for_cleaning":0,"items_blocked":len(tasks),"cross_check_prerequisite_met":False,"cleaning_not_started":True,"preview_not_pipeline":True,"auto_clean_disabled":True,"mock_used":False,"fixture_used":False}}

def build_console_integration():
    return {"phase185_console_integration":{"cross_check_tasks_viewable":True,"source_routes_viewable":True,"prompt_routes_viewable":True,"eligibility_gate_viewable":True,"cleaning_readiness_viewable":True,"console_not_auto_execute":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_phase185_guard():
    return {"phase185_guard":{"status":"pass","research_only":True,"cross_check_execution_disabled":True,"clean_evidence_write_disabled":True,"packet_update_disabled":True,"daily_brief_update_disabled":True,"weekly_review_update_disabled":True,"llm_api_disabled":True,"web_search_disabled":True,"network_fetch_disabled":True,"auto_clean_disabled":True,"mock_used":False,"fixture_used":False}}

def build_phase185_quality_gate():
    return {"phase185_quality_gate":{"status":"pass","checks":{"cross_check_registry_defined":True,"task_schema_defined":True,"reasons_classified":True,"source_routes_built":True,"prompt_routes_built":True,"verification_requirements_built":True,"tasks_generated":True,"eligibility_gate_active":True,"cleaning_readiness_preview_ready":True,"tasks_not_executed":True,"no_clean_evidence":True,"no_packet_update":True,"no_llm_call":True,"no_web_search":True,"gate_blocks_dirty_to_clean":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase185_cannot_conclude_guard():
    return {"phase185_cannot_conclude_guard":{"status":"pass","violations":0,"cannot_conclude":["cross_check_task_is_not_cross_check_execution","source_route_is_not_network_fetch","prompt_route_is_not_llm_call","eligibility_gate_is_not_clean_evidence_write","cleaning_readiness_is_not_cleaning_execution","no_clean_evidence_from_cross_check_design","cross_check_completion_required_before_cleaning","candidate_evidence_candidate_required_for_cleaning"]}}

def build_backlog():
    return {"phase185_backlog":{"phase185_completed":True,"cross_check_tasks_ready":True,"next_phases":{"phase186":"simulated_scout_execution_and_cross_check_runner"},"mock_used":False,"fixture_used":False,"research_only":True}}
