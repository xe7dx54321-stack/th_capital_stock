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
        "example_1_activate":{"candidate_id":"TSM","owner_decision":"activate_into_formal_research_coverage","rationale":"Dominant advanced foundry with structural AI demand tailwind. Evidence fill complete from SEC EDGAR and Yahoo Finance. Agent rerun passed with no trade language.","conditions":["tier_assignment_required","formal_thesis_writing_pending","valuation_model_building_pending"],"risk_acknowledgment":"Geopolitical risk requires ongoing monitoring; foundry capex cycle sensitivity noted.","why_valid":"Uses valid decision option, references research evidence, no trade language."},
        "example_2_keep":{"candidate_id":"INTC","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"Turnaround thesis requires observable execution milestones before formal coverage activation. Evidence filled but elevated risk noted by Risk Agent.","conditions":["quarterly_milestone_verification","foundry_customer_win_evidence"],"risk_acknowledgment":"Turnaround execution risk is high; formal coverage premature without milestone evidence.","why_valid":"Honest about evidence gaps, specific conditions, no false confidence."},
        "example_3_defer":{"candidate_id":"SNPS","owner_decision":"defer_to_next_review_cycle","rationale":"Ansys acquisition regulatory clearance pending; thesis contingent on outcome. Defer to avoid pre-judgment.","conditions":["ansys_regulatory_clearance","post_acquisition_integration_plan_review"],"risk_acknowledgment":"Regulatory risk may block acquisition; downside scenario requires contingency.","why_valid":"Defers appropriately when key binary event pending, no speculation."},
        "example_4_reject":{"candidate_id":"SNOW","owner_decision":"reject_from_current_coverage_pipeline","rationale":"Consumption revenue model making near-term trajectory unclear for formal coverage activation. Evidence gaps in customer retention metrics.","conditions":["consumption_revenue_stabilization","customer_retention_metric_improvement"],"risk_acknowledgment":"Consumption model sensitivity to macro environment may delay thesis formation.","why_valid":"Rejects with clear, evidence-based reasoning, not emotional."}
    }
    invalid_examples = {
        "invalid_1_trade":{"candidate_id":"MRVL","owner_decision":"buy","rationale":"Undervalued with 30% upside.","conditions":[],"risk_acknowledgment":"Standard disclaimer.","why_invalid":"owner_decision=buy is a trade action, not allowed. Rationale contains target price language. Risk acknowledgment is generic."},
        "invalid_2_target":{"candidate_id":"AMAT","owner_decision":"activate_into_formal_research_coverage","rationale":"Target price $250 by Q4.","conditions":[],"risk_acknowledgment":"N/A","why_invalid":"Rationale contains target price. Conditions and risk acknowledgment are empty/generic."},
        "invalid_3_incomplete":{"candidate_id":"","owner_decision":"","rationale":"","conditions":[],"risk_acknowledgment":"","why_invalid":"All required fields empty; candidate_id must match ticker list."}
    }
    return {"phase169_example_pack":{
        "valid_examples":valid_examples,"valid_example_count":len(valid_examples),
        "invalid_examples":invalid_examples,"invalid_example_count":len(invalid_examples),
        "total_examples":len(valid_examples)+len(invalid_examples),
        "mock_used":False,"fixture_used":False
    }}
