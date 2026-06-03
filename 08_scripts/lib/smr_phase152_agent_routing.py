def build_agent_routing(composite_result, bucket_result):
    scored = composite_result.get("composite_scores", [])
    routes = {"evidence_agent": [], "risk_agent": [], "judge_agent": []}
    for c in scored:
        scores = c.get("scores", {})
        ev = scores.get("evidence_readiness", {}).get("score", 5.0)
        rk = scores.get("risk_limitation_penalty", {}).get("score", 0.0)
        co = c["composite_score"]
        if ev < 3.0: routes["evidence_agent"].append({"ticker": c["ticker"], "reason": "evidence_below_3", "score": ev})
        if rk > 2.0: routes["risk_agent"].append({"ticker": c["ticker"], "reason": "risk_above_2", "score": rk})
        if co > 3.0: routes["judge_agent"].append({"ticker": c["ticker"], "reason": "composite_above_3", "score": co})
    return {"phase152_agent_routing": {
        "evidence_agent": {"candidates_routed": len(routes["evidence_agent"]), "routes": routes["evidence_agent"]},
        "risk_agent": {"candidates_routed": len(routes["risk_agent"]), "routes": routes["risk_agent"]},
        "judge_agent": {"candidates_routed": len(routes["judge_agent"]), "routes": routes["judge_agent"]},
        "agents_are_research_only": True, "mock_used": False, "fixture_used": False}}
