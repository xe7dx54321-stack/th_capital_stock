import json,os
def build_incident_escalation():
    result={
        "escalation_chain_defined":True,
        "severity_levels":["info","warning","critical","emergency"],
        "escalation_path":[
            {"level":"info","action":"log_and_continue","timeout_minutes":0},
            {"level":"warning","action":"notify_operator","timeout_minutes":15},
            {"level":"critical","action":"notify_supervisor_and_safe_mode","timeout_minutes":5},
            {"level":"emergency","action":"emergency_stop_and_notify_all","timeout_minutes":0}
        ],
        "readiness_status":"partial_ready",
        "blockers":["no_operator_contact_list","no_supervisor_escalation_contacts"],
        "allowed_next_action":"define_escalation_contact_roster",
        "no_order_created":True,"no_broker_action":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_incident_escalation":result}
