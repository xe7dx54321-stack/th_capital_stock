def build_homepage_link_update():
    links = []
    tickers = ["NVDA", "AVGO", "688041.SH", "300308.SZ", "002230.SZ", "09988.HK", "00700.HK", "300394.SZ"]
    for t in tickers:
        tid = t.replace(".", "-")
        links.append({"ticker": t, "href": f"phase142_ticker_details/{tid}.html", "label": f"{t} Detail"})
    links.append({"ticker": "_index", "href": "phase142_ticker_details/index.html", "label": "All Ticker Details"})
    return {"phase142_homepage_link_update": {"links": len(links), "ticker_links": links, "mock_used": False, "fixture_used": False}}
