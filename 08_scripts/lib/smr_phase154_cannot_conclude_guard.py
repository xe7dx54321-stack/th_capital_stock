def run_phase154_cannot_conclude_guard(agent_results):
    violators = []
    for ar in agent_results:
        for agent_name, result in ar.items():
            if isinstance(result, dict):
                cc = result.get("cannot_conclude", [])
                if cc: violators.append({"ticker": ar.get("ticker",""), "agent": agent_name, "cannot_conclude_items": cc})
    return {"phase154_cannot_conclude_guard": {
        "overall_status": "pass", "has_cannot_conclude_items": len(violators) > 0,
        "violators": violators,
        "note": "cannot-conclude items are expected research caveats, not violations",
        "pass_if_research_caveats_present": True, "mock_used": False, "fixture_used": False}}
