def build_agent_followup_routes(judge_result):
    summary = judge_result.get("summary", {})
    evidence_routes = []
    risk_routes = []
    for d in judge_result.get("decisions", []):
        if d["judge_decision"] == "needs_evidence_agent_follow_up":
            evidence_routes.append({"ticker": d["ticker"], "action": "gather_additional_evidence"})
        if d["judge_decision"] == "needs_risk_agent_follow_up":
            risk_routes.append({"ticker": d["ticker"], "action": "reassess_risks"})
    return {"phase153_agent_followup": {
        "evidence_agent_routes": len(evidence_routes), "evidence_routes": evidence_routes,
        "risk_agent_routes": len(risk_routes), "risk_routes": risk_routes,
        "agents_are_research_only": True, "mock_used": False, "fixture_used": False}}
