def build_post_approval_tasks(activation_plans):
    tasks = []
    for p in activation_plans.get("activation_plans",[]):
        tasks.append({"ticker":p["ticker"],"task":"onboarding_preparation","assigned_agent":"EvidenceAgent","status":"pending","contains_trade_action":False})
    return {"phase156_post_approval_tasks":{"tasks_generated":len(tasks),"tasks":tasks,"auto_execute":False,"requires_owner_approval":True,"mock_used":False,"fixture_used":False}}
