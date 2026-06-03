def run_opportunity_agent(targets):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "OpportunityAgent",
            "output": f"Opportunity scan for {t}: confirm admission route, check capacity, flag priority.",
            "priority_flag": "high" if t in ("NVDA","AVGO","MRVL","AMAT","LRCX") else "medium",
            "handoff_to": "EvidenceAgent",
            "cannot_conclude": ["opportunity_scan_is_simulation", "no_live_market_data"]})
    return {"phase154_opportunity_agent": {"targets_scanned": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
