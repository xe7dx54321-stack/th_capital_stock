def build_risk_register(targets):
    results = []
    for t in targets:
        ticker = t.get("ticker", "")
        risks = ["network_dependency: requires live network for actual data fetch"]
        if ticker in ["INTC"]:
            risks.append("turnaround_execution_risk: thesis depends on observable milestones")
        if ticker in ["SNPS"]:
            risks.append("regulatory_risk: Ansys acquisition pending regulatory clearance")
        results.append({
            "ticker": ticker,
            "risks": risks,
            "risk_level": "standard" if len(risks) <= 1 else "elevated",
            "limitations": ["data_not_yet_fetched_via_network", "skip_network_mode_active"],
            "cannot_conclude": ["data_availability_is_not_thesis_confirmation", "source_identified_is_not_research_complete"]
        })
    return {
        "phase162_risk_register": {
            "targets_checked": len(targets),
            "elevated_risk_tickers": sum(1 for r in results if r["risk_level"] == "elevated"),
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
