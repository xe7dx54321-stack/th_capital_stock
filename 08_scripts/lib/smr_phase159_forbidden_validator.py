def validate_no_forbidden_terms(parsed, forbidden):
    results = []
    for d in parsed.get("decisions",[]):
        rat = d.get("rationale",""); ticker = d.get("ticker","")
        found = [fw for fw in forbidden if fw.lower() in rat.lower()]
        results.append({"ticker":ticker,"forbidden_terms_found":found,"clean":len(found)==0,"error":f"Forbidden terms in rationale: {found}" if found else None})
    return {"phase159_forbidden_validator":{"validated":len(results),"all_clean":all(r["clean"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
