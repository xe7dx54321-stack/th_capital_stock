def build_phase156_backlog(candidates):
    entries = [{"ticker":c["ticker"],"status":"pending_owner_review","next":"awaiting_owner_decision"} for c in candidates]
    return {"phase156_backlog":{"entries":len(entries),"backlog":entries,"mock_used":False,"fixture_used":False}}
