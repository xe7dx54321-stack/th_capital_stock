def simulate_agent_task_queue(plan):
    tasks = [{"ticker":p["ticker"],"agent_tasks":["evidence_gathering","financial_loading","valuation_framework","thesis_drafting"],"auto_execute":False,"status":"pending_owner_sign_off"} for p in plan.get("execution_plans",[])]
    return {"phase157_agent_task_simulator":{"tasks_generated":len(tasks),"tasks":tasks,"simulation_only":True,"auto_execute":False,"mock_used":False,"fixture_used":False}}
