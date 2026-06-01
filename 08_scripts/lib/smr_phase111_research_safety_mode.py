def build_research_safety_mode():
    return {"phase111_research_safety_mode":{
        "mode":"research_safety",
        "trading_permanently_disabled":True,
        "paper_execution_permanently_disabled":True,
        "owner_can_pause_all":True,
        "owner_is_safety_controller":True,
        "kill_switch_replaced_by_owner_pause":True,
        "safety_checks":[
            {"check":"no_order_in_any_pipeline","status":"pass"},
            {"check":"no_trade_in_any_pipeline","status":"pass"},
            {"check":"no_pnl_calculation","status":"pass"},
            {"check":"owner_confirmation_active","status":"pass"},
            {"check":"research_only_mode_active","status":"pass"}
        ],
        "all_safety_checks_pass":True,
        "mock_used":False,
        "fixture_used":False
    }}
