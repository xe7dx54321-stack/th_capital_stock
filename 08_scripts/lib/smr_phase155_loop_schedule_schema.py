def build_loop_schedule_schema():
    return {"phase155_loop_schedule_schema":{"schedule_types":["daily","weekly","event_driven"],"schedule_fields":["schedule_id","schedule_type","target_tickers","assigned_agents","run_window","retry_policy","degraded_handling"],"system_scheduler_registration_allowed":False,"mock_used":False,"fixture_used":False}}
