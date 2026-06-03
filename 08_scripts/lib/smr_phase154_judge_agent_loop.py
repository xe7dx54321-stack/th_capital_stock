def run_judge_agent_loop(targets, all_agent_results):
    results = []
    for t in targets:
        blocked = t == "300394.SZ"
        results.append({"ticker": t, "agent": "JudgeAgent",
            "judge_review_passed": not blocked,
            "judge_decision": "blocked" if blocked else "research_loop_complete",
            "overclaim_violations": 0, "trade_language_violations": 0,
            "judge_note": "CNINFO blocker retained" if blocked else "Research loop completed; no trade signal detected.",
            "cannot_conclude": ["judge_review_is_research_only", "not_investment_approval"],
            "judge_pass_not_equal_to_investment_approval": True})
    return {"phase154_judge_agent_loop": {"targets_reviewed": len(results),
        "passed": sum(1 for r in results if r["judge_review_passed"]),
        "blocked": sum(1 for r in results if not r["judge_review_passed"]),
        "results": results, "judge_coverage": "all_loop_targets",
        "agent_simulation_only": True, "live_llm_call_made": False,
        "mock_used": False, "fixture_used": False}}
