def run_feedback_agent(targets, prev_results):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "FeedbackAgent",
            "output": f"Feedback for {t}: owner review items, checklist pending.",
            "feedback_items": ["confirm_thesis_direction","review_risk_assessment","sign_off_on_evidence_sufficiency"],
            "handoff_to": "JudgeAgent",
            "cannot_conclude": ["feedback_is_simulation", "no_owner_interaction"]})
    return {"phase154_feedback_agent": {"targets_with_feedback": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
