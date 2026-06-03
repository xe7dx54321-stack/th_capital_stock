def score_theme_fit(candidate):
    source = candidate.get("discovery_source", "")
    theme_map = {
        "theme_based": {"score": 5.0, "note": "directly theme-aligned"},
        "peer_based": {"score": 4.5, "note": "peer to covered ticker"},
        "industry_chain": {"score": 4.0, "note": "industry chain linkage"},
        "customer_capex": {"score": 3.5, "note": "customer capex beneficiary"},
        "news_event": {"score": 3.0, "note": "event-driven"},
        "financial_change": {"score": 3.0, "note": "financial-change triggered"},
        "product_roadmap": {"score": 4.0, "note": "product cycle alignment"},
        "supply_chain": {"score": 4.0, "note": "critical supply chain"},
        "external_public_lists": {"score": 2.5, "note": "external list; theme unverified"},
    }
    info = theme_map.get(source, {"score": 2.5, "note": "theme fit unverified"})
    return {
        "dimension": "theme_fit", "score": info["score"], "max_score": 5.0, "weight_multiplier": 1.5,
        "notes": [info["note"]],
        "cannot_conclude": ["theme_fit_not_manually_reviewed", "thesis_statement_not_written"],
        "mock_used": False, "fixture_used": False,
    }
