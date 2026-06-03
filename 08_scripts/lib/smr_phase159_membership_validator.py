def validate_candidate_membership(parsed, candidates):
    valid_tickers = {c["ticker"] for c in candidates}; results = []
    for d in parsed.get("decisions",[]):
        t = d.get("ticker","")
        results.append({"ticker":t,"is_known_candidate":t in valid_tickers,"error":None if t in valid_tickers else f"Unknown ticker: {t}"})
    return {"phase159_membership_validator":{"validated":len(results),"all_known":all(r["is_known_candidate"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
