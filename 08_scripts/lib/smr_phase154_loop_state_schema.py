def build_loop_state_schema():
    return {"phase154_loop_state_schema": {
        "loop_id": "phase154-loop-001", "loop_status": "simulation_only",
        "loop_state_fields": ["agent_id", "agent_role", "input_from_previous", "output",
                              "handoff_to_next", "judge_review_passed", "cannot_conclude_flags"],
        "agent_types": ["OpportunityAgent","EvidenceAgent","RiskAgent","ThesisAgent",
                       "DeepDiveAgent","BriefAgent","FeedbackAgent","JudgeAgent"],
        "simulation_disclaimer": "All agent outputs are structural templates, not live LLM calls.",
        "live_llm_call_made": False, "mock_used": False, "fixture_used": False,
    }}
