def build_task_queue():
    queue = [
        {"task_id": "TASK-146-001", "agent_id": "feedback_agent", "status": "pending", "priority": "low", "reason": "Awaiting owner feedback input", "blocker": None, "created_at": "2026-06-03T15:00:00Z"},
        {"task_id": "TASK-146-002", "agent_id": "deep_dive_agent", "status": "blocked", "priority": "medium", "reason": "300394 CNINFO org_id missing", "blocker": "cninfo_org_id_missing", "created_at": "2026-06-01T00:00:00Z"},
        {"task_id": "TASK-146-003", "agent_id": "evidence_agent", "status": "pending", "priority": "low", "reason": "Routine evidence refresh for all tickers", "blocker": None, "created_at": "2026-06-03T15:00:00Z"},
        {"task_id": "TASK-146-004", "agent_id": "risk_agent", "status": "pending", "priority": "low", "reason": "Re-scan gaps and source limitations", "blocker": None, "created_at": "2026-06-03T15:00:00Z"},
    ]
    summary = {"total": len(queue), "pending": sum(1 for q in queue if q["status"]=="pending"), "blocked": sum(1 for q in queue if q["status"]=="blocked"), "completed": 0}
    return {"phase146_task_queue": {"queue": queue, "summary": summary, "all_research_only": True, "mock_used": False, "fixture_used": False}}
