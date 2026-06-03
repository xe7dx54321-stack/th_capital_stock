def check_duplicates(parsed):
    tickers = [d.get("ticker","") for d in parsed.get("decisions",[])]
    seen = set(); dupes = []
    for t in tickers:
        if t in seen: dupes.append(t)
        seen.add(t)
    return {"phase159_duplicate_checker":{"duplicates_found":len(dupes),"duplicate_tickers":dupes,"no_duplicates":len(dupes)==0,"mock_used":False,"fixture_used":False}}
