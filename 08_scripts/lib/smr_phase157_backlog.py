def build_phase157_backlog(candidates):
    entries = [{"ticker":c["ticker"],"status":"pending_owner_decision","next":"awaiting_owner_input"} for c in candidates]
    return {"phase157_backlog":{"entries":len(entries),"backlog":entries,"mock_used":False,"fixture_used":False}}
