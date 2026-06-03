def build_evidence_followup_tasks(classified):
    tasks = []
    count = classified.get("more_evidence",0)
    for i in range(count):
        tasks.append({"task_id":f"ev-followup-{i+1}","action":"gather_additional_evidence","assigned_agent":"EvidenceAgent","status":"pending","contains_trade_action":False})
    return {"phase156_evidence_followup":{"tasks_generated":len(tasks),"tasks":tasks,"mock_used":False,"fixture_used":False}}
