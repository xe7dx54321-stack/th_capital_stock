def build_backlog_reframe():
    return {"phase111_backlog_reframe":{
        "mode":"personal_owner_research_copilot",
        "phase110_status":{"ready_for_paper_execution":False,"multi_user_assignment_required":False,"all_assignments_pending":False},
        "phase111_status":{"paper_execution_permanently_disabled":True,"multi_user_permanently_deprecated":True,"owner_mode_active":True},
        "backlog_items":[
            {"item":"opportunity_radar_v1","phase":"phase112","priority":"next","status":"queued"},
            {"item":"daily_monitoring_runner_refresh","phase":"ongoing","priority":"daily","status":"active"},
            {"item":"resolve_300394_blocker","phase":"future","priority":"medium","status":"blocked_by_cninfo"},
            {"item":"close_688041_valuation_gap","phase":"future","priority":"medium","status":"partial_available"},
            {"item":"watchlist_expansion","phase":"future","priority":"low","status":"pending"},
            {"item":"decision_journal","phase":"future","priority":"low","status":"pending"}
        ],
        "deprecated_items":[
            {"item":"assign_human_operators","reason":"multi_user_deprecated"},
            {"item":"activate_paper_execution","reason":"paper_execution_disabled"},
            {"item":"connect_broker","reason":"broker_integration_not_allowed"},
            {"item":"build_order_panel","reason":"no_orders_in_research_mode"}
        ],
        "next_recommended_action":"start_phase112_opportunity_radar_v1",
        "mock_used":False,
        "fixture_used":False
    }}
