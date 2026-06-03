def validate_allowed_decisions(parsed, allowed):
    results = []
    for d in parsed.get("decisions",[]):
        dec = d.get("decision","")
        results.append({"ticker":d.get("ticker",""),"decision":dec,"is_allowed":dec in allowed,"error":None if dec in allowed else f"Decision '{dec}' not in allowed set"})
    return {"phase159_decision_validator":{"validated":len(results),"all_allowed":all(r["is_allowed"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
