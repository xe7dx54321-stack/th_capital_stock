import json,os
def build_last_good_state_registry():
    result={
        "last_good_state_enabled":True,
        "snapshot_frequency":"manual_triggered",
        "snapshot_triggers":["pre_deploy","pre_config_change","daily","on_demand"],
        "state_includes":["config","risk_rules","approval_policies","source_health","db_connection_status","runner_status"],
        "retention_policy":"keep_last_30_snapshots",
        "readiness_status":"partial_ready",
        "blockers":["no_automated_snapshot_schedule"],
        "allowed_next_action":"configure_automated_snapshot_interval",
        "no_order_created":True,"mock_used":False,"fixture_used":False
    }
    return {"phase105_last_good_state_registry":result}
