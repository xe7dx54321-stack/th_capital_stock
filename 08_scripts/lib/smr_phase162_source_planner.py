def plan_candidate_source_routes(targets):
    source_routes = {
        "US_common_stock": {
            "primary": {"name": "SEC EDGAR", "url_pattern": "https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}", "requires_login": False, "free": True},
            "quote": {"name": "Yahoo Finance (no-login)", "url_pattern": "https://finance.yahoo.com/quote/{ticker}", "requires_login": False, "free": True},
            "news": {"name": "SEC 8-K filings", "url_pattern": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK={cik}&type=8-K", "requires_login": False, "free": True}
        }
    }
    results = []
    for t in targets:
        ticker = t.get("ticker", "")
        market = t.get("market", "")
        route = source_routes.get("US_common_stock", {})
        results.append({
            "ticker": ticker,
            "market": market,
            "primary_source": route.get("primary", {}).get("name", "unknown"),
            "quote_source": route.get("quote", {}).get("name", "unknown"),
            "news_source": route.get("news", {}).get("name", "unknown"),
            "all_free": True,
            "no_login_required": True,
            "skip_network_fallback": "source_identified_no_live_fetch"
        })
    return {
        "phase162_source_route_planner": {
            "targets_planned": len(targets),
            "all_routes_free": True,
            "all_routes_no_login": True,
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
