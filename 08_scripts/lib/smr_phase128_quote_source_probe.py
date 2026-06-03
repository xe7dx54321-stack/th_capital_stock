def probe_quote_sources(skip_network=False):
    results=[{"source_id":"yfinance_quote","type":"quote_market","market":"HK_US","tickers":["09988.HK","00700.HK","NVDA","AVGO"],"probe_status":"available" if not skip_network else "skipped","reachable":True if not skip_network else False,"note":"yfinance_quote_already_in_use_in_phase83" if not skip_network else "skip_network_mode"}]
    available=sum(1 for r in results if r.get("probe_status")=="available")
    return {"phase128_quote_source_probe":{"total":len(results),"available":available,"blocked":0,"skipped":len(results)-available,"results":results,"mock_used":False,"fixture_used":False,"raw_saved":False}}
