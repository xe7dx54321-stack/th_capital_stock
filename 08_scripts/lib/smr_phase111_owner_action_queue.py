def build_owner_action_queue():
    items=[
        {"action":"refresh_daily_monitoring","status":"auto_queued","requires_confirmation":False,"trade_action":False},
        {"action":"update_watch_board","status":"auto_queued","requires_confirmation":False,"trade_action":False},
        {"action":"write_evidence_memory","status":"auto_queued","requires_confirmation":False,"trade_action":False},
        {"action":"generate_research_brief","status":"auto_queued","requires_confirmation":False,"trade_action":False},
        {"action":"run_opportunity_radar","status":"queued","requires_confirmation":True,"trade_action":False},
        {"action":"resolve_300394_blocker","status":"blocked","requires_confirmation":True,"trade_action":False},
        {"action":"close_688041_valuation_gap","status":"queued","requires_confirmation":True,"trade_action":False}
    ]
    auto_queued=sum(1 for i in items if i["status"]=="auto_queued")
    queued=sum(1 for i in items if i["status"]=="queued")
    blocked=sum(1 for i in items if i["status"]=="blocked")
    no_trade=all(not i["trade_action"] for i in items)
    return {"phase111_owner_action_queue":{"total":len(items),"auto_queued":auto_queued,"queued":queued,"blocked":blocked,"no_trade_actions":no_trade,"paper_order_count":0,"live_trade_count":0,"items":items,"mock_used":False,"fixture_used":False}}
