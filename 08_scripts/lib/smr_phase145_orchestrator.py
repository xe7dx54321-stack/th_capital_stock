def build_orchestrator_state():
    tasks = [
        {"task_id": "TASK-145-opportunity_agent-001", "agent_id": "opportunity_agent", "task_type": "discovery", "status": "completed", "priority": "high", "outputs": {"tickers_scanned": 8, "opportunities_flagged": 0}},
        {"task_id": "TASK-145-evidence_agent-001", "agent_id": "evidence_agent", "task_type": "evidence_gathering", "status": "completed", "priority": "high", "outputs": {"evidence_updated": 8, "source_quality": "documented"}},
        {"task_id": "TASK-145-risk_agent-001", "agent_id": "risk_agent", "task_type": "risk_assessment", "status": "completed", "priority": "high", "outputs": {"risks_identified": 2, "gaps_documented": 5}},
        {"task_id": "TASK-145-thesis_agent-001", "agent_id": "thesis_agent", "task_type": "thesis_update", "status": "completed", "priority": "medium", "outputs": {"theses_updated": 8, "status_changes": 0}},
        {"task_id": "TASK-145-deep_dive_agent-001", "agent_id": "deep_dive_agent", "task_type": "deep_dive", "status": "completed", "priority": "medium", "outputs": {"deep_dives_completed": 2, "pending": 0}},
        {"task_id": "TASK-145-brief_agent-001", "agent_id": "brief_agent", "task_type": "brief", "status": "completed", "priority": "low", "outputs": {"brief_generated": True, "sections": 5}},
        {"task_id": "TASK-145-feedback_agent-001", "agent_id": "feedback_agent", "task_type": "feedback_routing", "status": "pending", "priority": "low", "outputs": None},
        {"task_id": "TASK-145-judge_agent-001", "agent_id": "judge_agent", "task_type": "audit", "status": "completed", "priority": "high", "outputs": {"audit_pass": True, "violations": 0}},
    ]
    summary = {
        "total_tasks": len(tasks),
        "completed": sum(1 for t in tasks if t["status"] == "completed"),
        "pending": sum(1 for t in tasks if t["status"] == "pending"),
        "failed": sum(1 for t in tasks if t["status"] == "failed"),
        "downgraded": sum(1 for t in tasks if t["status"] == "downgraded"),
        "all_research_only": True,
        "trade_actions": 0,
    }
    return {"phase145_orchestrator": {"tasks": tasks, "summary": summary, "auto_dispatch": False, "mock_used": False, "fixture_used": False}}
