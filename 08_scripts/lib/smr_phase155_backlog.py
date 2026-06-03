def build_phase155_backlog(targets):
    entries = [{"ticker":t,"status":"scheduled","next_run":"pending"} for t in targets]
    return {"phase155_backlog":{"entries":len(entries),"backlog":entries,"mock_used":False,"fixture_used":False}}
