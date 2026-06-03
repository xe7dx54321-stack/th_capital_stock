def score_owner_relevance(candidate):
    trigger = candidate.get("trigger", ""); name = candidate.get("name", "")
    ai_semi_kw = ["AI", "GPU", "semiconductor", "chip", "foundry", "ASIC", "HBM", "EDA", "equipment", "design"]
    score = 2.5; notes = []
    if any(kw.lower() in trigger.lower() or kw.lower() in name.lower() for kw in ai_semi_kw):
        score = 4.5; notes.append("aligns with owner AI/semiconductor focus")
    elif any(kw.lower() in trigger.lower() for kw in ["Cloud", "SaaS", "enterprise"]):
        score = 3.5; notes.append("aligns with owner tech/cloud interest")
    else: notes.append("owner relevance requires manual confirmation")
    return {
        "dimension": "owner_relevance", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["owner_relevance_not_manually_confirmed"],
        "mock_used": False, "fixture_used": False,
    }
