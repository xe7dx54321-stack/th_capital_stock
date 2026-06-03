def score_source_availability(candidate):
    source_map = {
        "US": {"primary": "SEC_EDGAR", "score": 5.0, "notes": "SEC EDGAR available"},
        "HK": {"primary": "HKEX", "score": 3.5, "notes": "HKEX available but limited"},
        "CN_A": {"primary": "CNINFO", "score": 2.0, "notes": "CNINFO requires org_id; may be blocked"},
    }
    market = candidate.get("market", "")
    info = source_map.get(market, {"primary": "unknown", "score": 1.0, "notes": "No known structured data source"})
    return {
        "dimension": "source_availability", "score": info["score"], "max_score": 5.0,
        "primary_source": info["primary"], "notes": [info["notes"]],
        "cannot_conclude": ["source_may_require_manual_access"],
        "mock_used": False, "fixture_used": False,
    }
