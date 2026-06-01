import json,os
def build_rollback_manifest_schema():
    schema={
        "manifest_id":"required, uuid",
        "emergency_id":"required, fk to emergency incident",
        "triggered_by":"required, operator_id or system",
        "triggered_at":"required, iso8601",
        "rollback_type":"required, enum: [config, data, state, connection, full]",
        "pre_state":"required, last_good_state_reference",
        "post_state":"required, expected state after rollback",
        "steps":"required, ordered list of rollback steps",
        "verification":"required, how to verify rollback success",
        "status":"required, enum: [pending, in_progress, complete, failed]",
        "no_order_created":True,"no_trade_created":True
    }
    return {"phase105_rollback_manifest_schema":{"schema":schema,"readiness_status":"partial_ready","blockers":["rollback_procedure_not_tested"],"mock_used":False,"fixture_used":False}}
