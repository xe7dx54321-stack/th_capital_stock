def score_activation_effort(candidate):
    market = candidate.get("market", "")
    if market == "US": score = 1.5; notes = ["US onboarding low effort"]
    elif market == "HK": score = 3.0; notes = ["HK onboarding medium effort"]
    elif market == "CN_A": score = 4.0; notes = ["CN_A onboarding high effort"]
    else: score = 4.5; notes = ["unknown market: high effort"]
    return {
        "dimension": "activation_effort", "score": score, "max_score": 5.0, "higher_is_better": False,
        "notes": notes, "cannot_conclude": ["effort_estimate_based_on_market_only"],
        "mock_used": False, "fixture_used": False,
    }
