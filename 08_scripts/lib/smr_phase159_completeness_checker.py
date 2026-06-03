def check_completeness(parsed):
    results = []
    for d in parsed.get("decisions",[]):
        has_ticker = bool(d.get("ticker"))
        has_decision = bool(d.get("decision"))
        has_rationale = bool(d.get("rationale","").strip())
        complete = has_ticker and has_decision and has_rationale
        results.append({"ticker":d.get("ticker","unknown"),"complete":complete,"missing":[] if complete else [f for f,ok in [("ticker",has_ticker),("decision",has_decision),("rationale",has_rationale)] if not ok]})
    return {"phase159_completeness_checker":{"checked":len(results),"all_complete":all(r["complete"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
