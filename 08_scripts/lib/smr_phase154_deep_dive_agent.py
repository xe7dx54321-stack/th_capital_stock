def run_deep_dive_agent(targets, prev_results):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "DeepDiveAgent",
            "output": f"Deep dive plan for {t}: revenue, margin, R&D trend; competitive position; valuation framework.",
            "deep_dive_tasks": ["revenue_trend_analysis","margin_analysis","rd_intensity_check","competitive_positioning","valuation_framework"],
            "handoff_to": "BriefAgent",
            "cannot_conclude": ["deep_dive_is_plan_not_execution", "no_new_financial_data_fetched"]})
    return {"phase154_deep_dive_agent": {"targets_planned": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
