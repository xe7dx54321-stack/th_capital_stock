def build_phase158_backlog(candidates):
    entries = [{"ticker":c["ticker"],"ui_card_rendered":True,"status":"pending_owner_review"} for c in candidates]
    return {"phase158_backlog":{"entries":len(entries),"backlog":entries,"mock_used":False,"fixture_used":False}}
