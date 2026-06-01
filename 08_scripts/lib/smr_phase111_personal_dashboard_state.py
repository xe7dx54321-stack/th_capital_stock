def build_personal_dashboard_state():
    return {"phase111_personal_dashboard_state":{
        "mode":"personal_owner_dashboard",
        "research_only_view":True,
        "no_trading_panels":True,
        "active_views":["watch_board","signal_monitor","coverage_matrix","brief_reader","opportunity_radar_placeholder"],
        "disabled_views":["order_panel","position_panel","pnl_panel","trade_history","broker_status","approval_queue","supervisor_panel"],
        "owner_actions_available":True,
        "owner_confirmation_required_for":["opportunity_discovery","valuation_analysis","thesis_update"],
        "blocked_tickers":["300394.SZ"],
        "partial_tickers":["688041.SH"],
        "next_phase_hint":"phase112_opportunity_radar_v1",
        "mock_used":False,
        "fixture_used":False
    }}
