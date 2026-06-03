def score_catalyst_novelty(candidate):
    source = candidate.get("discovery_source", ""); trigger = candidate.get("trigger", "")
    ai_keywords = ["AI", "GPU", "ASIC", "semiconductor", "foundry", "HBM", "EDA", "Agent", "Cloud"]
    score = 2.5; notes = []
    if any(kw.lower() in trigger.lower() for kw in ai_keywords): score = 4.0; notes.append("AI/semiconductor catalyst")
    if source == "product_roadmap": score = max(score, 4.0); notes.append("product roadmap catalyst")
    if source == "customer_capex": score = max(score, 3.5); notes.append("capex cycle catalyst")
    if not notes: notes.append("catalyst assessment pending manual review")
    return {
        "dimension": "catalyst_novelty", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["catalyst_requires_manual_assessment"],
        "mock_used": False, "fixture_used": False,
    }
