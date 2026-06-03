def validate_schema(parsed):
    decisions = parsed.get("decisions",[])
    results = []
    for d in decisions:
        valid = isinstance(d,dict) and "ticker" in d and "decision" in d
        results.append({"ticker":d.get("ticker","unknown"),"schema_valid":valid,"error":None if valid else "missing required field: ticker or decision"})
    return {"phase159_schema_validator":{"validated":len(results),"all_valid":all(r["schema_valid"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
