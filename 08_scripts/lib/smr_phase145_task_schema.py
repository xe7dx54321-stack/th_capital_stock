def build_task_schema():
    schema = {
        "task_id": "string, format: TASK-{phase}-{agent_id}-{seq}",
        "agent_id": "string, one of registered agent IDs",
        "task_type": "string: discovery | evidence_gathering | risk_assessment | thesis_update | deep_dive | brief | feedback_routing | audit",
        "status": "string: pending | dispatched | running | completed | failed | downgraded | skipped",
        "priority": "string: high | medium | low",
        "inputs": "object, agent-specific input payload",
        "outputs": "object, agent-specific output payload (populated on completion)",
        "dependencies": "list of task_ids that must complete first",
        "assigned_at": "ISO datetime",
        "started_at": "ISO datetime",
        "completed_at": "ISO datetime",
        "downgrade_reason": "string, populated if status=downgraded",
        "retry_count": "int, default 0",
        "max_retries": "int, default 1",
        "research_only": True,
        "trade_actions_blocked": True
    }
    return {"phase145_task_schema": {"schema": schema, "mock_used": False, "fixture_used": False}}
