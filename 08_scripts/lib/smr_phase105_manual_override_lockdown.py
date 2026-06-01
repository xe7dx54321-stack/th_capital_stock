import json,os
def build_manual_override_lockdown():
    result={
        "override_lockdown_enabled":True,
        "cannot_override":["kill_switch","emergency_stop","safe_mode_disable_live","safe_mode_disable_order"],
        "can_override_with_dual_auth":["safe_mode_read_only","report_access","dashboard_view"],
        "override_requires_audit":True,
        "override_requires_incident_ticket":True,
        "readiness_status":"ready",
        "no_order_created":True,"no_trade_created":True,"no_broker_action":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_manual_override_lockdown":result}
