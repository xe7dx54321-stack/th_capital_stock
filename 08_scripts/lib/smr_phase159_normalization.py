def normalize_submission(parsed):
    norm = []
    for d in parsed.get("decisions",[]):
        norm.append({"ticker":d.get("ticker","").strip().upper(),"decision":d.get("decision","pending_owner_review").strip(),"rationale":d.get("rationale","").strip(),"requested_tier":d.get("requested_tier","candidate").strip()})
    return {"phase159_normalization":{"normalized":len(norm),"decisions":norm,"mock_used":False,"fixture_used":False}}
