def build_risk_review_packet(candidate):
    market = candidate.get("market", ""); source = candidate.get("discovery_source", "")
    risks = ["market_risk", "company_specific_risk"]
    if market != "US": risks.append(f"non_US_market_risk_{market}")
    if source in ("news_event", "financial_change"): risks.append("transient_relevance_risk")
    return {"packet_type": "risk_limitation_review", "ticker": candidate["ticker"],
        "known_risks": risks, "risk_mitigation_notes": ["Manual review recommended before activation"],
        "cannot_conclude": ["risk_assessment_requires_manual_review"],
        "mock_used": False, "fixture_used": False}
