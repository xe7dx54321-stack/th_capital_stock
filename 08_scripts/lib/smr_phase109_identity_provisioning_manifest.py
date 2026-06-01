import json,os
def build_identity_provisioning_manifest():
    manifest={
        "roles_to_provision":["operator","reviewer","approver","supervisor","kill_switch_operator"],
        "minimum_operators_per_role":{"operator":1,"reviewer":1,"approver":2,"supervisor":1,"kill_switch_operator":1},
        "provisioning_status":"not_started",
        "real_accounts_created":0,
        "sso_integration_status":"not_started",
        "sso_connections":0,
        "blockers":["requires_human_decision_on_personnel","requires_offline_identity_verification"],
        "allowed_next_action":"human_assignment_of_operator_identities"
    }
    return {"phase109_identity_provisioning_manifest":{"manifest":manifest,"mock_used":False,"fixture_used":False}}
