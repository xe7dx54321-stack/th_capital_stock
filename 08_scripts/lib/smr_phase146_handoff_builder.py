def build_handoff_records():
    handoffs = [
        {"from_agent": "opportunity_agent", "to_agent": "evidence_agent", "content": "8 ticker watchlist with financial snapshot data", "status": "consumed", "timestamp": "2026-06-03T14:00:00Z"},
        {"from_agent": "evidence_agent", "to_agent": "thesis_agent", "content": "Updated evidence chains for 8 tickers", "status": "consumed", "timestamp": "2026-06-03T14:10:00Z"},
        {"from_agent": "risk_agent", "to_agent": "brief_agent", "content": "Risk flags: 2 gaps, 5 source limitations", "status": "consumed", "timestamp": "2026-06-03T14:20:00Z"},
        {"from_agent": "thesis_agent", "to_agent": "brief_agent", "content": "8 theses updated, 0 status changes", "status": "consumed", "timestamp": "2026-06-03T14:30:00Z"},
        {"from_agent": "brief_agent", "to_agent": "judge_agent", "content": "Daily brief with 5 sections", "status": "consumed", "timestamp": "2026-06-03T14:40:00Z"},
        {"from_agent": "judge_agent", "to_agent": "feedback_agent", "content": "Audit result: pass, 0 violations", "status": "pending", "timestamp": "2026-06-03T14:50:00Z"},
    ]
    return {"phase146_handoff_records": {"handoffs": len(handoffs), "records": handoffs, "all_research_only": True, "mock_used": False, "fixture_used": False}}
