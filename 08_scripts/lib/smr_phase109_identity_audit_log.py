import json,os
def build_identity_audit_log_schema():
    schema={
        "log_id":"required, uuid",
        "timestamp":"required, iso8601",
        "operator_id":"required",
        "action":"required",
        "role":"required at time of action",
        "dual_control_partner":"required if dual_control_action",
        "result":"required",
        "immutable":True
    }
    return {"phase109_identity_audit_log":{"schema":schema,"readiness_status":"ready","mock_used":False,"fixture_used":False}}
