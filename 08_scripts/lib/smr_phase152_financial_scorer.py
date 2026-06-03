def score_financial_route_readiness(candidate):
    market = candidate.get("market", "")
    if market == "US": score = 4.5; notes = ["SEC EDGAR 10-K/10-Q available"]
    elif market == "HK": score = 3.0; notes = ["HKEX filings available, HKD/USD normalisation needed"]
    elif market == "CN_A": score = 2.0; notes = ["CNINFO dependent, CNY normalisation needed"]
    else: score = 1.0; notes = ["no known financial route"]
    return {
        "dimension": "financial_route_readiness", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["specific_financial_metrics_not_verified"],
        "mock_used": False, "fixture_used": False,
    }
