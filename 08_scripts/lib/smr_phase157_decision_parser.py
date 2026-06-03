def parse_owner_decisions(imported):
    decisions = imported.get("decisions",[])
    parsed = []
    for d in decisions:
        parsed.append({"ticker":d.get("ticker",""),"decision":d.get("decision","pending_owner_review"),"rationale":d.get("rationale",""),"parsed_ok":True})
    return {"phase157_decision_parser":{"parsed":len(parsed),"decisions":parsed,"mock_used":False,"fixture_used":False}}
