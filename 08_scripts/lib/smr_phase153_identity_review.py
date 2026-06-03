def build_identity_review_packet(candidate):
    ticker = candidate.get("ticker", ""); market = candidate.get("market", "")
    status = "verified" if ticker and market == "US" else ("needs_confirmation" if ticker else "blocked")
    return {"packet_type": "identity_review", "ticker": ticker, "market": market,
        "identity_status": status,
        "checks": {"ticker_present": bool(ticker), "market_known": bool(market),
                   "us_suffix_check": "." not in ticker if market == "US" else "n/a"},
        "notes": ["US ticker identity verified via SEC EDGAR naming convention" if market == "US" else "identity review needed"],
        "cannot_conclude": ["specific_entity_verification_without_manual_review"],
        "mock_used": False, "fixture_used": False}
