def build_dependency_graph():
    graph = {
        "opportunity_agent": {"depends_on": [], "feeds_into": ["evidence_agent", "risk_agent"]},
        "evidence_agent": {"depends_on": ["opportunity_agent"], "feeds_into": ["thesis_agent", "risk_agent", "judge_agent"]},
        "risk_agent": {"depends_on": ["opportunity_agent", "evidence_agent"], "feeds_into": ["brief_agent", "judge_agent"]},
        "thesis_agent": {"depends_on": ["evidence_agent"], "feeds_into": ["brief_agent", "feedback_agent"]},
        "deep_dive_agent": {"depends_on": ["risk_agent", "feedback_agent"], "feeds_into": ["evidence_agent", "thesis_agent"]},
        "brief_agent": {"depends_on": ["thesis_agent", "risk_agent", "evidence_agent"], "feeds_into": ["judge_agent"]},
        "feedback_agent": {"depends_on": ["brief_agent"], "feeds_into": ["thesis_agent", "deep_dive_agent"]},
        "judge_agent": {"depends_on": ["evidence_agent", "risk_agent", "brief_agent"], "feeds_into": []},
    }
    return {"phase145_dependency_graph": {"graph": graph, "agents": len(graph), "mock_used": False, "fixture_used": False}}
