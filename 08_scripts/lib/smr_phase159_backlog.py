def build_phase159_backlog(candidates):
    entries = [{"ticker":c["ticker"],"submission_status":"pending_owner_input","validated":False} for c in candidates]
    return {"phase159_backlog":{"entries":len(entries),"backlog":entries,"mock_used":False,"fixture_used":False}}
