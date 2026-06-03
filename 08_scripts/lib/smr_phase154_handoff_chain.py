def build_handoff_chain():
    chain = [
        {"from": "OpportunityAgent", "to": "EvidenceAgent", "handoff_type": "scan_to_evidence"},
        {"from": "EvidenceAgent", "to": "RiskAgent", "handoff_type": "evidence_to_risk"},
        {"from": "RiskAgent", "to": "ThesisAgent", "handoff_type": "risk_to_thesis"},
        {"from": "ThesisAgent", "to": "DeepDiveAgent", "handoff_type": "thesis_to_deep_dive"},
        {"from": "DeepDiveAgent", "to": "BriefAgent", "handoff_type": "plan_to_brief"},
        {"from": "BriefAgent", "to": "FeedbackAgent", "handoff_type": "brief_to_feedback"},
        {"from": "FeedbackAgent", "to": "JudgeAgent", "handoff_type": "feedback_to_judge"},
    ]
    return {"phase154_handoff_chain": {"chain_length": len(chain), "chain": chain,
        "handoff_required": True, "mock_used": False, "fixture_used": False}}
