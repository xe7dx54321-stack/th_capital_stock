def score_risk_penalty(candidate):
    market = candidate.get("market", ""); source = candidate.get("discovery_source", "")
    score = 2.0; notes = []
    if market == "CN_A": score = 3.0; notes.append("CN_A CNINFO blocker risk")
    elif market == "HK": score = 2.5; notes.append("HKEX source limitation risk")
    if source == "external_public_lists": score = max(score, 3.0); notes.append("higher identity/source risk")
    if source == "news_event": score = max(score, 2.5); notes.append("transient relevance risk")
    if not notes: notes.append("baseline risk")
    return {
        "dimension": "risk_limitation_penalty", "score": score, "max_score": 5.0, "higher_is_better": False,
        "weight_multiplier": -0.5, "notes": notes,
        "cannot_conclude": ["risk_assessment_requires_manual_review"],
        "mock_used": False, "fixture_used": False,
    }
