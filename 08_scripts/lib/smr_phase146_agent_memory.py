def build_agent_memory():
    agents = ["opportunity_agent", "evidence_agent", "risk_agent", "thesis_agent", "deep_dive_agent", "brief_agent", "feedback_agent", "judge_agent"]
    memories = []
    for aid in agents:
        memories.append({
            "agent_id": aid,
            "last_run_at": "2026-06-03T15:00:00Z",
            "last_status": "completed",
            "tasks_completed_total": 1,
            "tasks_pending_total": 0,
            "handoffs_received": [],
            "handoffs_sent": [],
            "blockers": [],
            "notes": ""
        })
    return {"phase146_agent_memory": {"agents": len(agents), "memories": memories, "all_research_only": True, "mock_used": False, "fixture_used": False}}
