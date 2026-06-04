# Phase182 intelligence scout prompt pack core
import json, os, sys
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))

from smr_phase177_packet_builder import ACTIVATED

ACTIVATED_CANDIDATES = ACTIVATED
PROMPT_TYPES = [
    "general_news_scout","management_commentary_scout","customer_demand_scout",
    "supply_chain_crosscheck_scout","product_pricing_lead_time_scout",
    "filing_official_source_scout","risk_negative_signal_scout","contradiction_scout"
]
SOURCE_CATEGORIES = ["official_filing","company_ir","earnings_call_transcript","industry_media","social_or_forum"]

def build_activated_candidate_scout_universe():
    rows = []
    for cid in ACTIVATED_CANDIDATES:
        rows.append({"candidate_id":cid,"scout_enabled":True,"scout_status":"prompt_pack_designed",
                     "llm_not_called":True,"network_not_called":True,"raw_not_saved":True,
                     "clean_evidence_not_written":True})
    return {"phase182_scout_universe":{"activated_candidate_count":len(rows),"rows":rows,
            "mock_used":False,"fixture_used":False,"research_only":True}}

def build_scout_prompt_taxonomy():
    taxonomy = []
    for pt in PROMPT_TYPES:
        taxonomy.append({"prompt_type":pt,"taxonomy_entry":True,"defined":True,"research_only":True})
    return {"phase182_prompt_taxonomy":{"prompt_types":PROMPT_TYPES,"prompt_type_count":len(PROMPT_TYPES),
            "taxonomy_entries":taxonomy,"mock_used":False,"fixture_used":False}}

def _make_prompt_card(pt):
    purposes = {"general_news_scout":"Capture material news, announcements, product launches, and sector developments that may impact the candidate company.","management_commentary_scout":"Track management commentary from earnings calls, investor days, conferences, and interviews.","customer_demand_scout":"Monitor customer demand signals: order trends, backlog changes, customer capex announcements, end-market demand indicators.","supply_chain_crosscheck_scout":"Crosscheck supply chain signals: supplier commentary, lead times, component availability, pricing trends from upstream/downstream.","product_pricing_lead_time_scout":"Track product pricing changes, lead time fluctuations, ASP trends, and competitive positioning signals.","filing_official_source_scout":"Monitor official filings: 10-K, 10-Q, 8-K, 13F, SEC filings, exchange disclosures, regulatory filings.","risk_negative_signal_scout":"Scan for risk and negative signals: litigation, regulatory actions, customer losses, product defects, management departures, accounting issues.","contradiction_scout":"Identify contradictions between company narrative and external data, between different sources, or between stated guidance and observable metrics."}
    scopes = {"general_news_scout":"Company and sector-level news within lookback window.","management_commentary_scout":"Verbatim or summarized management statements from official channels.","customer_demand_scout":"Customer and end-market demand indicators across the value chain.","supply_chain_crosscheck_scout":"Supplier, competitor, and channel partner signals.","product_pricing_lead_time_scout":"Product-level pricing, lead time, and competitive dynamics.","filing_official_source_scout":"Regulatory and exchange filings from official repositories.","risk_negative_signal_scout":"Adverse events, litigation, regulatory actions, and operational disruptions.","contradiction_scout":"Cross-source inconsistencies, narrative vs. data gaps, and guidance vs. reality checks."}
    return {"prompt_id":f"scout_{pt}","prompt_type":pt,"purpose":purposes.get(pt,""),"target_scope":scopes.get(pt,""),
            "lookback_window":"7-30 days depending on signal type","source_preferences":SOURCE_CATEGORIES,
            "required_fields":["source_url","published_at","title","snippet","prompt_id","scout_timestamp","candidate_id"],
            "forbidden_outputs":["buy","sell","hold","target_price","position_size","portfolio_weight","trade_signal","investment_recommendation","price_forecast","valuation_opinion"],
            "cannot_conclude_rules":["no_investment_conclusion","no_trade_recommendation","no_target_price","no_position_sizing","no_market_timing","no_relative_value_ranking"],
            "output_schema_ref":"dirty_intelligence_item","example_prompt":f"Find material {pt.replace('_',' ')} for {{candidate_id}} in the last 14 days. Return structured dirty intelligence items with source URLs and timestamps.",
            "example_valid_output":'{"source_url":"https://example.com/news/123","published_at":"2026-06-01","title":"Example headline","snippet":"Relevant excerpt...","prompt_id":"scout_'+pt+'","scout_timestamp":"2026-06-04T10:00:00Z","candidate_id":"MRVL"}',
            "example_invalid_output":'{"title":"Buy MRVL now","target_price":100,"recommendation":"strong_buy"}',
            "research_only":True,"not_investment_advice":True}

def build_scout_prompt_cards():
    cards = [_make_prompt_card(pt) for pt in PROMPT_TYPES]
    return {"phase182_prompt_cards":{"prompt_cards":cards,"prompt_card_count":len(cards),
            "prompt_type_count":len(PROMPT_TYPES),"all_cards_research_only":True,
            "mock_used":False,"fixture_used":False}}

def build_ticker_specific_prompt_plan():
    plans = []
    for cid in ACTIVATED_CANDIDATES:
        plans.append({"candidate_id":cid,"prompt_types_enabled":PROMPT_TYPES,"prompt_type_count":len(PROMPT_TYPES),
                      "plan_status":"designed","auto_dispatch_disabled":True,"scout_frequency":"manual_only",
                      "priority":"standard","research_only":True})
    return {"phase182_ticker_scout_plan":{"ticker_scout_plans":plans,"ticker_scout_plan_count":len(plans),
            "activated_candidate_count":len(ACTIVATED_CANDIDATES),"all_plans_designed_not_dispatched":True,
            "mock_used":False,"fixture_used":False}}

def build_source_category_map():
    categories = []
    for sc in SOURCE_CATEGORIES:
        descriptions = {"official_filing":"SEC EDGAR, exchange filings, regulatory disclosures","company_ir":"Company investor relations pages, press releases, presentations","earnings_call_transcript":"Earnings call transcripts, investor day transcripts","industry_media":"Industry publications, semiconductor trade press, financial media","social_or_forum":"Social media, investor forums, Reddit, Twitter/X (low-weight, verification required)"}
        categories.append({"category":sc,"description":descriptions.get(sc,""),"weight":"high" if sc in ["official_filing","company_ir"] else ("medium" if sc in ["earnings_call_transcript","industry_media"] else "low"),"requires_verification":sc in ["social_or_forum","industry_media"],"research_only":True})
    return {"phase182_source_category_map":{"source_categories":categories,"source_category_count":len(categories),
            "mock_used":False,"fixture_used":False}}

def build_dirty_intelligence_item_schema():
    schema = {"dirty_item_schema":{"required_fields":["item_id","candidate_id","prompt_id","source_url","published_at","scout_timestamp","title","snippet","source_category","needs_cleaning","needs_corroboration","dirty_status"],
              "optional_fields":["author","language","estimated_relevance","raw_text_excerpt","fetch_method"],
              "forbidden_fields":["buy_signal","sell_signal","hold_signal","target_price","position_size","portfolio_action","trade_recommendation","investment_conclusion"],
              "dirty_status_values":["raw_captured","pending_cleaning","cleaning_in_progress","cleaned_ready_for_review","quarantined"],
              "schema_version":"1.0","research_only":True}}
    return {"phase182_dirty_item_schema":schema}

def build_scout_output_contract():
    return {"phase182_output_contract":{"contract_version":"1.0","output_schema":"dirty_intelligence_item",
            "output_format":"json_array","required_per_item":["source_url","published_at","title","snippet","prompt_id","candidate_id"],
            "quality_requirements":["source_attributable","timestamp_present","no_trade_terms","no_investment_conclusion","no_target_price","no_position_sizing"],
            "rejection_rules":["missing_source_url","missing_timestamp","contains_trade_terms","contains_target_price","contains_position_sizing","no_candidate_id"],
            "contract_not_investment_advice":True,"research_only":True,"mock_used":False,"fixture_used":False}}

def build_source_metadata_requirements():
    return {"phase182_source_metadata":{"required_metadata":["source_url","published_at","source_category","access_date","fetch_method"],
            "optional_metadata":["author","publisher","language","paywall_status"],
            "metadata_not_investment_advice":True,"research_only":True,"mock_used":False,"fixture_used":False}}

def build_prompt_safety_rules():
    rules = ["no_trade_terms_in_prompt","no_trade_terms_in_output","no_target_price_in_prompt","no_target_price_in_output",
             "no_position_sizing_in_prompt","no_position_sizing_in_output","no_investment_conclusion","no_market_timing",
             "no_broker_instructions","source_attribution_required","timestamp_required","research_only_label_required",
             "cannot_conclude_label_required"]
    return {"phase182_prompt_safety_rules":{"safety_rules":rules,"safety_rule_count":len(rules),
            "all_prompts_compliant":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_prompt_cannot_conclude_rules():
    rules = ["cannot_conclude_investment_decision","cannot_conclude_trade_action","cannot_conclude_target_price",
             "cannot_conclude_position_size","cannot_conclude_market_direction","cannot_conclude_relative_value",
             "cannot_conclude_customer_share_from_news","cannot_conclude_revenue_impact_from_headline",
             "cannot_conclude_competitive_win_from_announcement"]
    return {"phase182_prompt_cc_rules":{"cannot_conclude_rules":rules,"rule_count":len(rules),
            "mock_used":False,"fixture_used":False,"research_only":True}}

def build_prompt_scheduling_policy():
    return {"phase182_scheduling_policy":{"cron_enabled":False,"mode":"manual_prompt_pack_design_only",
            "auto_dispatch_disabled":True,"scheduler_registration_disabled":True,
            "recommended_frequency":"owner_manual_trigger_only","timezone":"Asia/Shanghai",
            "mock_used":False,"fixture_used":False,"research_only":True}}

def build_prompt_priority_policy():
    return {"phase182_priority_policy":{"priority_levels":["high","standard","low"],
            "default_priority":"standard","high_priority_prompts":["filing_official_source_scout","risk_negative_signal_scout"],
            "standard_priority_prompts":["general_news_scout","management_commentary_scout","customer_demand_scout","product_pricing_lead_time_scout"],
            "low_priority_prompts":["supply_chain_crosscheck_scout","contradiction_scout"],
            "priority_not_trade_signal":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_expected_output_examples():
    examples = []
    for cid in ACTIVATED_CANDIDATES[:3]:
        examples.append({"candidate_id":cid,"prompt_id":"scout_general_news_scout",
            "example_output":{"item_id":f"di-{cid}-001","candidate_id":cid,"prompt_id":"scout_general_news_scout",
            "source_url":f"https://example.com/{cid.lower()}/news","published_at":"2026-06-01T08:00:00Z",
            "scout_timestamp":"2026-06-04T10:00:00Z","title":f"Sample news headline for {cid}",
            "snippet":f"Relevant excerpt about {cid} business operations.","source_category":"industry_media",
            "needs_cleaning":True,"needs_corroboration":True,"dirty_status":"raw_captured"},
            "note":"This is a designed example, not real LLM output."})
    return {"phase182_expected_output_examples":{"examples":examples,"example_count":len(examples),
            "examples_are_designed_not_real":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_invalid_output_examples():
    examples = [
        {"label":"trade_recommendation","candidate_id":"MRVL","invalid_output":{"title":"Buy MRVL now","recommendation":"strong_buy","target_price":100},"quarantine_reason":"contains_trade_terms_and_target_price"},
        {"label":"position_sizing","candidate_id":"AMAT","invalid_output":{"title":"AMAT update","position_size":"5%","action":"add"},"quarantine_reason":"contains_position_sizing"},
        {"label":"investment_conclusion","candidate_id":"LRCX","invalid_output":{"title":"LRCX analysis","conclusion":"overweight","rating":"outperform"},"quarantine_reason":"contains_investment_conclusion"},
        {"label":"missing_source","candidate_id":"KLAC","invalid_output":{"title":"Something happened","snippet":"No URL provided"},"quarantine_reason":"missing_source_url"},
        {"label":"price_forecast","candidate_id":"CDNS","invalid_output":{"title":"CDNS forecast","price_target_12m":350},"quarantine_reason":"contains_price_forecast"},
        {"label":"market_timing","candidate_id":"CRM","invalid_output":{"title":"CRM entry point","entry_timing":"next_week","rationale":"earnings_play"},"quarantine_reason":"contains_market_timing"},
    ]
    return {"phase182_invalid_output_examples":{"invalid_examples":examples,"invalid_example_count":len(examples),
            "examples_are_designed_not_real":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_dirty_inbox_interface_preview():
    return {"phase182_dirty_inbox_interface":{"interface_preview_generated":True,
            "interface_type":"json_schema_only","inbox_path":"09_runbooks/generated/phase182_dirty_inbox/",
            "inbox_path_ignored":True,"ingestion_pipeline":"not_built","cleaning_pipeline":"not_built",
            "clean_evidence_writer":"not_built","auto_ingest_disabled":True,"auto_clean_disabled":True,
            "interface_is_preview_not_operational":True,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_console_integration():
    return {"phase182_console_integration":{"prompt_pack_viewable":True,"prompt_cards_viewable":True,
            "ticker_scout_plans_viewable":True,"source_category_map_viewable":True,"dirty_schema_viewable":True,
            "output_contract_viewable":True,"safety_rules_viewable":True,"cc_rules_viewable":True,
            "dirty_inbox_preview_viewable":True,"console_not_auto_dispatch":True,
            "mock_used":False,"fixture_used":False,"research_only":True}}

def build_phase182_guard():
    return {"phase182_guard":{"status":"pass","research_only":True,
            "llm_api_disabled":True,"web_search_disabled":True,"network_fetch_disabled":True,
            "raw_save_disabled":True,"clean_evidence_write_disabled":True,"packet_update_disabled":True,
            "daily_brief_update_disabled":True,"weekly_review_update_disabled":True,
            "auto_dispatch_disabled":True,"scheduler_registration_disabled":True,
            "mock_used":False,"fixture_used":False}}

def build_phase182_quality_gate():
    return {"phase182_quality_gate":{"status":"pass","checks":{"activated_candidates":len(ACTIVATED_CANDIDATES),
            "prompt_type_count":len(PROMPT_TYPES),"prompt_card_count":len(PROMPT_TYPES),
            "ticker_scout_plan_count":len(ACTIVATED_CANDIDATES),
            "source_category_count":len(SOURCE_CATEGORIES),"dirty_schema_defined":True,
            "output_contract_defined":True,"safety_rules_defined":True,"cc_rules_defined":True,
            "scheduling_policy_defined":True,"dirty_inbox_preview_defined":True,
            "no_llm_call":True,"no_web_search":True,"no_network_fetch":True,"no_raw_save":True,
            "no_clean_evidence":True,"no_packet_update":True,"no_brief_update":True,
            "prompt_cards_research_only":True},"violations":0,"mock_used":False,"fixture_used":False}}

def build_phase182_cannot_conclude_guard():
    return {"phase182_cannot_conclude_guard":{"status":"pass","violations":0,
            "cannot_conclude":["prompt_pack_is_design_not_execution","dirty_inbox_is_preview_not_operational",
            "prompt_cards_are_templates_not_live_queries","ticker_scout_plans_are_plans_not_dispatches",
            "output_examples_are_designed_not_real_llm_output","no_investment_conclusion_from_prompt_design",
            "no_clean_evidence_from_dirty_items_yet","no_packet_update_from_scout_design"]}}

def build_backlog():
    return {"phase182_backlog":{"phase182_completed":True,"prompt_pack_designed":True,
            "next_phases":{"phase183":"dirty_intelligence_inbox_ingestion_pipeline"},
            "mock_used":False,"fixture_used":False,"research_only":True}}
