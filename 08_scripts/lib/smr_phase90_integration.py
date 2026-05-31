def build_scheduled_integration():
    from smr_phase90_preflight import run_preflight
    from smr_phase90_scheduler import build_scheduler_commands
    from smr_phase90_delivery_builder import build_delivery_artifacts
    from smr_phase90_failure_report import build_failure_report
    from smr_phase90_notification import build_notification_status
    pf=run_preflight();sc=build_scheduler_commands();dl=build_delivery_artifacts();fr=build_failure_report();nt=build_notification_status()
    return {"phase90_scheduled_integration":{"preflight_status":pf["phase90_preflight"]["overall"],"preflight_checks":pf["phase90_preflight"]["checks_count"],"scheduler_commands":sc["phase90_scheduler_commands"]["mode"],"delivery_artifacts":len(dl["phase90_delivery_builder"]["artifacts"]),"failure_scenarios":fr["phase90_failure_report"]["scenarios_defined"],"notification_adapters_enabled":nt["phase90_notification_adapters"]["enabled"],"watch_only":True,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
