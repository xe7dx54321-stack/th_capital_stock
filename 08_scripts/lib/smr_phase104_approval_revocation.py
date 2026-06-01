import json,os
def build_approval_revocation():
    result={
        "revocation_enabled":True,
        "max_revocation_window_hours":72,
        "revocation_reasons":["error_in_request","new_information","risk_change","operator_request"],
        "requires_audit_trail":True,
        "requires_supervisor_if_operator_initiated":True,
        "readiness_status":"partial_ready",
        "blockers":["revocation_audit_trail_schema_pending"],
        "allowed_next_action":"define_revocation_audit_trail",
        "no_order_created":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_approval_revocation":result}
