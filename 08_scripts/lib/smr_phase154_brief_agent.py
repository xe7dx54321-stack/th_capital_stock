def run_brief_agent(targets, prev_results):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "BriefAgent",
            "output": f"Brief draft for {t}: observed-only summary, no buy/sell, no target price.",
            "brief_sections": ["summary","financial_trend","thesis_status","risk_flags","owner_actions","cannot_conclude"],
            "handoff_to": "FeedbackAgent",
            "cannot_conclude": ["brief_is_research_only", "no_trade_advice"]})
    return {"phase154_brief_agent": {"briefs_drafted": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
