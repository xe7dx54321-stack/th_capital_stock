def build_financial_route_review_packet(candidate):
    market = candidate.get("market", "")
    if market == "US": ready = True; notes = ["SEC 10-K/10-Q provides standardized financials", "USD; no currency conversion needed"]
    elif market == "HK": ready = True; notes = ["HKEX filings available", "HKD/USD conversion may be needed"]
    else: ready = False; notes = ["financial route not confirmed for this market"]
    return {"packet_type": "financial_route_review", "ticker": candidate["ticker"], "market": market,
        "financial_route_ready": ready, "notes": notes,
        "route_ready_not_equal_to_financials_loaded": True,
        "cannot_conclude": ["financials_not_loaded", "specific_metrics_not_verified"],
        "mock_used": False, "fixture_used": False}
