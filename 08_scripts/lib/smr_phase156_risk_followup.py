def build_risk_followup_tasks(classified):
    tasks = []
    count = classified.get("identity_confirmation",0) + classified.get("source_confirmation",0)
    for i in range(count):
        tasks.append({"task_id":f"risk-followup-{i+1}","action":"reassess_risks","assigned_agent":"RiskAgent","status":"pending","contains_trade_action":False})
    return {"phase156_risk_followup":{"tasks_generated":len(tasks),"tasks":tasks,"mock_used":False,"fixture_used":False}}
