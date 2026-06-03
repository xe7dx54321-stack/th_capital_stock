def build_task_queue_update(targets):
    tasks = []
    for t in targets:
        tasks.append({"ticker": t, "task_type": "agent_loop_complete", "status": "done",
                      "next_action": "owner_review_pending"})
    return {"phase154_task_queue_update": {"tasks_generated": len(tasks), "tasks": tasks,
        "mock_used": False, "fixture_used": False}}
