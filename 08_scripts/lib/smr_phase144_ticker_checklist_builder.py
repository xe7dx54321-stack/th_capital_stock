def build_ticker_checklists():
    tickers = ["NVDA", "AVGO", "688041.SH", "300308.SZ", "002230.SZ", "09988.HK", "00700.HK", "300394.SZ"]
    checklists = []
    for t in tickers:
        checklists.append({
            "ticker": t,
            "items": [
                "Financial data reviewed and current",
                "Thesis status assessed by owner",
                "Evidence chain reviewed for gaps",
                "Source limitations acknowledged",
                "Owner actions clearly defined",
                "Deep dive status current",
                "Ready for monitoring continuation"
            ],
            "notes_field": True,
            "signature_field": True,
            "date_field": True
        })
    return {"phase144_ticker_checklists": {"tickers": len(tickers), "checklists": checklists, "mock_used": False, "fixture_used": False}}
