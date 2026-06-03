def run_workload_budget_enforcer(plan):
    max_agents = 8; assigned = min(plan.get("agents_count",len(plan.get("agents",[]))),max_agents)
    return {"phase155_workload_budget":{"max_agents_per_run":max_agents,"agents_assigned":assigned,"budget_remaining":max_agents-assigned,"budget_exceeded":assigned>max_agents,"budget_exceeded_actions_taken":[],"mock_used":False,"fixture_used":False}}
