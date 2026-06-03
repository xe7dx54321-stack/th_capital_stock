def score_identity_confidence(candidate):
    ticker = candidate.get("ticker", "")
    market = candidate.get("market", "")
    score = 5.0; notes = []
    if not ticker: score = 0.0; notes.append("no_ticker_provided")
    if market not in ("US", "HK", "CN_A"): score = min(score, 3.0); notes.append("market_less_familiar")
    if "." not in ticker and market == "US": score = min(score, 4.0); notes.append("us_ticker_no_suffix_acceptable")
    return {
        "dimension": "identity_confidence", "score": score, "max_score": 5.0,
        "notes": notes if notes else ["identity_normalized"],
        "cannot_conclude": ["specific_entity_verification_without_manual_review"] if score < 4 else [],
        "mock_used": False, "fixture_used": False,
    }
