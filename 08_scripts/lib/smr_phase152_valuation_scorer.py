def score_valuation_route_readiness(candidate):
    market = candidate.get("market", "")
    if market == "US": score = 4.0; notes = ["P/E, EV/EBITDA, P/S feasible with SEC data"]
    elif market == "HK": score = 3.0; notes = ["basic multiples feasible, HKEX limits depth"]
    elif market == "CN_A": score = 2.0; notes = ["valuation feasible if financial data available, may be derived label only"]
    else: score = 1.0; notes = ["valuation route unclear"]
    return {
        "dimension": "valuation_route_readiness", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["specific_valuation_multiple_not_calculated", "valuation_is_derived_label_only"],
        "mock_used": False, "fixture_used": False,
    }
