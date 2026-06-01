import json,os
def build_two_step_approval():
    result={
        "two_step_required":True,
        "step1":{"role":"operator","action":"review_and_approve","status":"defined"},
        "step2":{"role":"supervisor","action":"validate_and_approve","status":"defined"},
        "separation_of_duties":True,
        "no_auto_escalation":True,
        "blockers":["operator_identity_not_provisioned","supervisor_identity_not_provisioned"],
        "readiness_status":"partial_ready",
        "allowed_next_action":"provision_operator_and_supervisor_identities",
        "no_order_created":True,
        "no_trade_created":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_two_step_approval":result}
