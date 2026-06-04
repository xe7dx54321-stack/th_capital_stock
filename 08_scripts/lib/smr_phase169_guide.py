CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]

def build_fill_guide():
    return {"phase169_fill_guide":{
        "title":"Owner Decision Input Fill Guide",
        "fields":{
            "candidate_id":{"type":"string","required":True,"description":"Ticker symbol exactly as listed in candidate universe. Must be one of the 13 candidates.","valid_example":"MRVL","invalid_example":"NVDA (not in candidate universe)"},
            "owner_decision":{"type":"string","required":True,"description":"Choose exactly one from the 4 allowed options. NOT buy/sell/hold.","valid_example":"activate_into_formal_research_coverage","invalid_example":"buy (trade action, not allowed)","options":VALID_DECISIONS},
            "rationale":{"type":"string","required":True,"description":"Brief rationale for decision. Must reference research evidence, not price target or profit expectation.","valid_example":"Evidence fill complete, agent rerun passed, AI infrastructure exposure thesis identified.","invalid_example":"Stock will go up 20% in 6 months."},
            "conditions":{"type":"array","required":True,"description":"Conditions that must be met before real activation.","valid_example":["tier_assignment_required","formal_thesis_writing_pending"]},
            "risk_acknowledgment":{"type":"string","required":True,"description":"Acknowledge key risks. Must reference specific risks, not generic disclaimers.","valid_example":"INTC turnaround execution risk requires quarterly milestone monitoring.","invalid_example":"Past performance does not guarantee future results."}
        },
        "rules":[
            "NO buy/sell/hold/short/add/reduce in any field",
            "NO target price in any field",
            "NO position sizing in any field",
            "NO trade recommendations in any field",
            "ALL 13 candidates must be covered",
            "Each candidate_id must exactly match ticker list"
        ],
        "mock_used":False,"fixture_used":False
    }}

def build_example_pack():
    valid_examples = {
        "example_1_activate":{"candidate_id":"TSM","owner_decision":"activate_into_formal_research_coverage","rationale":"Dominant advanced foundry with structural AI demand tailwind. Evidence fill complete from SEC EDGAR and Yahoo Finance. Agent rerun passed with no trade language.","conditions":["tier_assignment_required","formal_thesis_writing_pending","valuation_model_building_pending"],"risk_acknowledgment":"Geopolitical risk requires ongoing monitoring; foundry capex cycle sensitivity noted.","why_valid":"Uses valid decision option, references research evidence, no trade language.","expectation":"expected_valid_count=13,expected_invalid_count=0,expected_quarantine_count=0,expected_activation_execution=0,watch_core_updated=false,expected_reason=single_valid_activate"},
        "example_2_keep":{"candidate_id":"INTC","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"Turnaround thesis requires observable execution milestones before formal coverage activation. Evidence filled but elevated risk noted by Risk Agent.","conditions":["quarterly_milestone_verification","foundry_customer_win_evidence"],"risk_acknowledgment":"Turnaround execution risk is high; formal coverage premature without milestone evidence.","why_valid":"Honest about evidence gaps, specific conditions, no false confidence.","expectation":"expected_valid_count=13,expected_invalid_count=0,expected_quarantine_count=0,expected_activation_execution=0,watch_core_updated=false,expected_reason=single_valid_keep"},
        "example_3_defer":{"candidate_id":"SNPS","owner_decision":"defer_to_next_review_cycle","rationale":"Ansys acquisition regulatory clearance pending; thesis contingent on outcome. Defer to avoid pre-judgment.","conditions":["ansys_regulatory_clearance","post_acquisition_integration_plan_review"],"risk_acknowledgment":"Regulatory risk may block acquisition; downside scenario requires contingency.","why_valid":"Defers appropriately when key binary event pending, no speculation.","expectation":"expected_valid_count=13,expected_invalid_count=0,expected_quarantine_count=0,expected_activation_execution=0,watch_core_updated=false,expected_reason=single_valid_defer"},
        "example_4_reject":{"candidate_id":"SNOW","owner_decision":"reject_from_current_coverage_pipeline","rationale":"Consumption revenue model making near-term trajectory unclear for formal coverage activation. Evidence gaps in customer retention metrics.","conditions":["consumption_revenue_stabilization","customer_retention_metric_improvement"],"risk_acknowledgment":"Consumption model sensitivity to macro environment may delay thesis formation.","why_valid":"Rejects with clear, evidence-based reasoning, not emotional.","expectation":"expected_valid_count=13,expected_invalid_count=0,expected_quarantine_count=0,expected_activation_execution=0,watch_core_updated=false,expected_reason=single_valid_reject"},
        "example_5_mixed_all_13":{
            "decisions":[
                {"candidate_id":"TSM","owner_decision":"activate_into_formal_research_coverage","rationale":"Dominant foundry; structural AI demand.","conditions":["tier_assignment"],"risk_acknowledgment":"Geopolitical risk."},
                {"candidate_id":"ASML","owner_decision":"activate_into_formal_research_coverage","rationale":"EUV monopoly; capex tailwind.","conditions":["tier_assignment"],"risk_acknowledgment":"Cycle risk."},
                {"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"Custom ASIC leader.","conditions":["tier_assignment"],"risk_acknowledgment":"Customer concentration."},
                {"candidate_id":"AMAT","owner_decision":"activate_into_formal_research_coverage","rationale":"Equipment leader.","conditions":["tier_assignment"],"risk_acknowledgment":"Capex cycle."},
                {"candidate_id":"LRCX","owner_decision":"activate_into_formal_research_coverage","rationale":"Etch and deposition process leader.","conditions":["tier_assignment"],"risk_acknowledgment":"Capex cycle."},
                {"candidate_id":"KLAC","owner_decision":"activate_into_formal_research_coverage","rationale":"Process control leader.","conditions":["tier_assignment"],"risk_acknowledgment":"Node transition risk."},
                {"candidate_id":"CDNS","owner_decision":"activate_into_formal_research_coverage","rationale":"EDA leader with Synopsys dynamics.","conditions":["competitive_monitoring"],"risk_acknowledgment":"Competitive risk."},
                {"candidate_id":"CRM","owner_decision":"activate_into_formal_research_coverage","rationale":"SaaS leader with Agentforce AI thesis.","conditions":["revenue_trajectory_verification"],"risk_acknowledgment":"Enterprise spending cycle."},
                {"candidate_id":"AMD","owner_decision":"activate_into_formal_research_coverage","rationale":"GPU/CPU competitor in AI inference.","conditions":["market_share_verification"],"risk_acknowledgment":"Competitive intensity."},
                {"candidate_id":"INTC","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"Turnaround milestones needed.","conditions":["quarterly_milestones"],"risk_acknowledgment":"Turnaround execution risk."},
                {"candidate_id":"SNPS","owner_decision":"defer_to_next_review_cycle","rationale":"Ansys clearance pending.","conditions":["regulatory_clearance"],"risk_acknowledgment":"Regulatory risk."},
                {"candidate_id":"MU","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"Memory cycle timing needs assessment.","conditions":["cycle_timing"],"risk_acknowledgment":"Cyclical risk."},
                {"candidate_id":"SNOW","owner_decision":"reject_from_current_coverage_pipeline","rationale":"Consumption model unclear.","conditions":["revenue_stabilization"],"risk_acknowledgment":"Model sensitivity."}
            ],
            "why_valid":"Covers all 13 candidates with mixed decisions; no trade terms; each has rationale, conditions, and risk acknowledgment.",
            "expectation":"expected_valid_count=13,expected_invalid_count=0,expected_quarantine_count=0,expected_activation_execution=0,watch_core_updated=false,expected_reason=mixed_all_13_valid",
            "schema_valid":True,"safety_valid":True,"trade_terms":0,"target_price_terms":0,"position_terms":0,"expected_valid_count":13,"expected_invalid_count":0,"expected_quarantine_count":0,"expected_activation_execution":0,"watch_core_updated":False
        }
    }
    invalid_examples = {
        "invalid_1_trade_buy":{
            "candidate_id":"MRVL","owner_decision":"buy","rationale":"Undervalued with 30% upside.","conditions":[],"risk_acknowledgment":"Standard disclaimer.",
            "why_invalid":"owner_decision=buy is a trade action, not allowed. Rationale contains target price language. Risk acknowledgment is generic.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"trade_like_terms","quarantine_reason":"trade_like_terms"
        },
        "invalid_2_target_price":{
            "candidate_id":"AMAT","owner_decision":"activate_into_formal_research_coverage","rationale":"Target price $250 by Q4. Position sizing 5%.","conditions":[],"risk_acknowledgment":"N/A",
            "why_invalid":"Rationale contains target_price and position_sizing. Conditions and risk acknowledgment are empty/generic.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"target_or_position_terms","quarantine_reason":"target_or_position_terms"
        },
        "invalid_3_incomplete":{
            "candidate_id":"","owner_decision":"","rationale":"","conditions":[],"risk_acknowledgment":"",
            "why_invalid":"All required fields empty; candidate_id must match ticker list.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"missing_required_field","quarantine_reason":"missing_required_field"
        },
        "invalid_4_unknown_candidate":{
            "candidate_id":"NVDA","owner_decision":"activate_into_formal_research_coverage","rationale":"AI leader.","conditions":[],"risk_acknowledgment":"Standard risk.",
            "why_invalid":"candidate_id=NVDA is not in the 13-candidate universe. Must match ticker list exactly.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"unknown_candidate","quarantine_reason":"unknown_candidate"
        },
        "invalid_5_duplicate_candidate":{
            "decisions":[
                {"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":["x"],"risk_acknowledgment":"ok"},
                {"candidate_id":"MRVL","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"duplicate","conditions":["x"],"risk_acknowledgment":"ok"}
            ],
            "why_invalid":"Duplicate candidate_id=MRVL appears twice. Each candidate must appear exactly once.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"duplicate_candidate","quarantine_reason":"duplicate_candidate"
        },
        "invalid_6_bad_option":{
            "candidate_id":"MRVL","owner_decision":"strong_buy_recommendation","rationale":"Looks great!","conditions":[],"risk_acknowledgment":"ok",
            "why_invalid":"owner_decision=strong_buy_recommendation is not one of the 4 allowed decision options.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"invalid_decision_option","quarantine_reason":"invalid_decision_option"
        },
        "invalid_7_missing_rationale":{
            "candidate_id":"LRCX","owner_decision":"activate_into_formal_research_coverage","rationale":"","conditions":["x"],"risk_acknowledgment":"ok",
            "why_invalid":"rationale is empty. Every decision must include a rationale referencing research evidence.",
            "expected_quarantine":True,"expected_invalid_count":1,"expected_activation_execution":0,"expected_watch_core_update":False,"expected_reason":"missing_rationale","quarantine_reason":"missing_rationale"
        }
    }
    return {"phase169_example_pack":{
        "valid_examples":valid_examples,"valid_example_count":len(valid_examples),"valid_examples_exceed_minimum":len(valid_examples)>=5,
        "invalid_examples":invalid_examples,"invalid_example_count":len(invalid_examples),"invalid_examples_exceed_minimum":len(invalid_examples)>=6,
        "total_examples":len(valid_examples)+len(invalid_examples),
        "mock_used":False,"fixture_used":False
    }}

