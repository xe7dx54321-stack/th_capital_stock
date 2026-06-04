CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_formal_research_state_preview(validator_output):
    v = validator_output["phase170_schema_validator"]
    previews = []
    for e in v.get("valid",[]):
        activated = e["owner_decision"] == "activate_into_formal_research_coverage"
        previews.append({
            "candidate_id":e["candidate_id"],
            "decision":e["owner_decision"],
            "formal_state_preview":"would_enter_formal_research_coverage" if activated else "would_remain_candidate",
            "state_not_updated":True,"preview_not_execution":True,
            "cannot_conclude":["state_preview_is_not_state_update","formal_preview_is_not_activation"]
        })
    return {"phase170_formal_research_state_preview":{"entries":len(previews),"state_not_updated":True,"preview_not_execution":True,"previews":previews,"mock_used":False,"fixture_used":False}}

def build_tier_proposal_preview(validator_output):
    v = validator_output["phase170_schema_validator"]
    proposals = []
    for e in v.get("valid",[]):
        tier = "proposed_tier_1" if e["owner_decision"] == "activate_into_formal_research_coverage" else "proposed_tier_candidate"
        proposals.append({"candidate_id":e["candidate_id"],"proposed_tier":tier,"tier_not_assigned":True,"tier_proposal_not_execution":True,"cannot_conclude":["tier_proposal_is_not_tier_assignment","tier_is_not_investment_rating"]})
    return {"phase170_tier_proposal_preview":{"entries":len(proposals),"tier_not_assigned":True,"tier_proposal_not_execution":True,"proposals":proposals,"mock_used":False,"fixture_used":False}}

def build_agent_task_delta(validator_output):
    v = validator_output["phase170_schema_validator"]
    tasks = []
    for e in v.get("valid",[]):
        activated = e["owner_decision"] == "activate_into_formal_research_coverage"
        task = "initiate_formal_thesis_writing" if activated else "continue_monitoring"
        tasks.append({"candidate_id":e["candidate_id"],"agent_task":task,"task_not_executed":True,"agent_tasks_not_trade":True,"cannot_conclude":["agent_task_is_not_trade_instruction","task_delta_is_not_execution"]})
    return {"phase170_agent_task_delta":{"entries":len(tasks),"task_not_executed":True,"agent_tasks_not_trade":True,"tasks":tasks,"mock_used":False,"fixture_used":False}}

def build_daily_monitoring_preview(validator_output):
    v = validator_output["phase170_schema_validator"]
    previews = []
    for e in v.get("valid",[]):
        activated = e["owner_decision"] == "activate_into_formal_research_coverage"
        previews.append({"candidate_id":e["candidate_id"],"daily_monitoring":"would_be_added" if activated else "would_continue_existing","monitoring_not_updated":True,"cannot_conclude":["monitoring_preview_is_not_monitoring_update"]})
    return {"phase170_daily_monitoring_preview":{"entries":len(previews),"monitoring_not_updated":True,"previews":previews,"mock_used":False,"fixture_used":False}}
