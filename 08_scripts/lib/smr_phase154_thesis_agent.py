def run_thesis_agent(targets, prev_results):
    results = []
    for t in targets:
        results.append({"ticker": t, "agent": "ThesisAgent",
            "output": f"Thesis proposal for {t}: seed thesis based on discovery source, unconfirmed.",
            "thesis_status": "unconfirmed", "thesis_seed": f"Research thesis for {t} based on existing coverage themes.",
            "handoff_to": "DeepDiveAgent",
            "cannot_conclude": ["thesis_is_simulation", "thesis_unconfirmed", "no_customer_order_data"]})
    return {"phase154_thesis_agent": {"targets_processed": len(results), "results": results,
        "confirmed_thesis_created": False, "agent_simulation_only": True,
        "live_llm_call_made": False, "mock_used": False, "fixture_used": False}}
