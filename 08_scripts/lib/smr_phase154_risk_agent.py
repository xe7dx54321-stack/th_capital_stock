def run_risk_agent(targets, prev_results):
    results = []
    for t in targets:
        is_blocked = t == "300394.SZ"
        results.append({"ticker": t, "agent": "RiskAgent",
            "output": f"Risk screen for {t}: {'CNINFO blocker detected' if is_blocked else 'baseline risks identified'}.",
            "blocked": is_blocked, "blocker": "cninfo_org_id_missing" if is_blocked else None,
            "risk_flags": ["market_risk","liquidity_risk"] if not is_blocked else ["cninfo_blocker"],
            "handoff_to": "ThesisAgent",
            "cannot_conclude": ["risk_assessment_is_simulation"]})
    return {"phase154_risk_agent": {"targets_screened": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
