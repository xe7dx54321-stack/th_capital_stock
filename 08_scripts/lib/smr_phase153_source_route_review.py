def build_source_route_review_packet(candidate):
    market = candidate.get("market", "")
    routes = {"US": "SEC_EDGAR_10K_10Q", "HK": "HKEX_FILINGS", "CN_A": "CNINFO_SZSE_SSE"}
    route = routes.get(market, "unknown")
    ready = market == "US"
    return {"packet_type": "source_route_review", "ticker": candidate["ticker"], "market": market,
        "primary_source": route, "source_route_ready": ready,
        "notes": ["SEC EDGAR route confirmed" if ready else f"Source route: {route} - may need manual confirmation"],
        "route_ready_not_equal_to_data_loaded": True,
        "cannot_conclude": ["source_not_accessed", "source_capacity_not_verified"],
        "mock_used": False, "fixture_used": False}
