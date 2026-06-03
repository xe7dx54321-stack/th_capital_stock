def build_next_task_scheduler(targets):
    tasks = []
    for t in targets:
        tasks.append({"ticker":t,"next_task":"owner_review_pending","scheduled_after":"owner_approval","contains_trade_action":False})
    return {"phase155_next_task_scheduler":{"tasks_scheduled":len(tasks),"tasks":tasks,"next_tasks_are_not_trade_actions":True,"mock_used":False,"fixture_used":False}}
