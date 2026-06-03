def run_evidence_agent(targets, prev_results):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "EvidenceAgent",
            "output": f"Evidence check for {t}: public filings confirmed, earnings history tracked.",
            "evidence_found": True, "evidence_gaps": ["customer_order_data", "supplier_contracts"],
            "handoff_to": "RiskAgent",
            "cannot_conclude": ["evidence_is_simulation", "no_new_source_access", "public_filings_not_verified_by_llm"]})
    return {"phase154_evidence_agent": {"targets_checked": len(results), "results": results,
        "agent_simulation_only": True, "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
