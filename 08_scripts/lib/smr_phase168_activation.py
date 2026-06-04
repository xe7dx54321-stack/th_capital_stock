CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
VALID_DECISIONS = ["activate_into_formal_research_coverage","keep_as_candidate_pending_more_evidence","defer_to_next_review_cycle","reject_from_current_coverage_pipeline"]

def build_activation_simulator(submitted_input=None):
    simulations = []
    activated = 0
    kept = 0
    deferred = 0
    rejected = 0
    for tk in CANDIDATES:
        decision = "PENDING_OWNER_INPUT"
        if submitted_input:
            for d in submitted_input.get("decisions", []):
                if d.get("candidate_id") == tk:
                    decision = d.get("owner_decision", decision)
        if decision == "activate_into_formal_research_coverage": activated += 1
        elif decision == "keep_as_candidate_pending_more_evidence": kept += 1
        elif decision == "defer_to_next_review_cycle": deferred += 1
        elif decision == "reject_from_current_coverage_pipeline": rejected += 1
        else: kept += 1
        simulations.append({
            "ticker": tk,
            "decision": decision,
            "simulated_outcome": "would_enter_formal_coverage" if decision == "activate_into_formal_research_coverage" else "would_remain_candidate",
            "simulation_not_real_execution": True,
            "watch_core_not_updated": True,
            "cannot_conclude": ["simulation_is_not_real_activation","simulated_outcome_is_not_portfolio_action"]
        })
    return {"phase168_activation_simulator":{"candidates":len(simulations),"simulation_only":True,"real_activation_executed":False,"watch_core_updated":False,"activated_count":activated,"kept_count":kept,"deferred_count":deferred,"rejected_count":rejected,"simulations":simulations,"mock_used":False,"fixture_used":False}}

def build_coverage_proposal_builder(simulator_output):
    proposals = []
    for s in simulator_output["phase168_activation_simulator"]["simulations"]:
        if s["decision"] == "activate_into_formal_research_coverage":
            proposals.append({
                "ticker": s["ticker"],
                "proposal": "activate_to_formal_research_coverage",
                "conditions": ["tier_assignment_pending","formal_thesis_writing_pending","owner_final_confirmation_pending"],
                "coverage_proposal_not_portfolio_action":True,
                "cannot_conclude":["proposal_is_not_activation","coverage_is_not_investment_recommendation"]
            })
    return {"phase168_coverage_proposal_builder":{"proposals":len(proposals),"coverage_proposal_not_portfolio_action":True,"no_buy_sell_hold":True,"proposal_items":proposals,"mock_used":False,"fixture_used":False}}
