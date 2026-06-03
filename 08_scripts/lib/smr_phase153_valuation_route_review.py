def build_valuation_route_review_packet(candidate):
    market = candidate.get("market", "")
    if market == "US": ready = True; notes = ["P/E, EV/EBITDA, P/S feasible with SEC data"]
    elif market == "HK": ready = True; notes = ["basic multiples feasible"]
    else: ready = False; notes = ["valuation route unclear"]
    return {"packet_type": "valuation_route_review", "ticker": candidate["ticker"], "market": market,
        "valuation_route_ready": ready, "notes": notes,
        "route_ready_not_equal_to_valuation_computed": True,
        "valuation_label_is_derived_only": True,
        "cannot_conclude": ["specific_valuation_multiple_not_calculated", "target_price_not_computed"],
        "mock_used": False, "fixture_used": False}
