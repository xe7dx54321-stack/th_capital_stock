def resolve_candidate_identities(targets):
    results = []
    identity_map = {
        "MRVL": {"cik": "0001835632", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "01-31"},
        "AMAT": {"cik": "0000695155", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "10-31"},
        "LRCX": {"cik": "0000707549", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "06-30"},
        "KLAC": {"cik": "0000319201", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "06-30"},
        "INTC": {"cik": "0000050863", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "12-31"},
        "SNPS": {"cik": "0000883241", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "10-31"},
        "CDNS": {"cik": "0000813672", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "12-31"},
        "CRM": {"cik": "0001108524", "exchange": "NYSE", "currency": "USD", "fiscal_year_end": "01-31"},
        "TSM": {"cik": "0001046179", "exchange": "NYSE", "currency": "USD", "fiscal_year_end": "12-31"},
        "ASML": {"cik": "0000937966", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "12-31"},
        "AMD": {"cik": "0000002488", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "12-31"},
        "SNOW": {"cik": "0001640147", "exchange": "NYSE", "currency": "USD", "fiscal_year_end": "01-31"},
        "MU": {"cik": "0000723125", "exchange": "NASDAQ", "currency": "USD", "fiscal_year_end": "08-31"}
    }
    for t in targets:
        ticker = t.get("ticker", "")
        info = identity_map.get(ticker, {})
        results.append({
            "ticker": ticker,
            "name": t.get("name", ""),
            "market": t.get("market", ""),
            "cik": info.get("cik", "unknown"),
            "exchange": info.get("exchange", "unknown"),
            "currency": info.get("currency", "unknown"),
            "fiscal_year_end": info.get("fiscal_year_end", "unknown"),
            "identity_resolved": bool(info),
            "resolution_source": "manual_mapping"
        })
    resolved = sum(1 for r in results if r["identity_resolved"])
    return {
        "phase162_identity_resolver": {
            "targets_checked": len(targets),
            "identities_resolved": resolved,
            "identities_unresolved": len(targets) - resolved,
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
