import json,os
def build_operator_identity():
    result={
        "identity_required":True,
        "roles_defined":["operator","supervisor","admin"],
        "identity_store":"not_provisioned",
        "rbac_configured":False,
        "authentication_method":"not_configured",
        "readiness_status":"not_ready",
        "blockers":["no_identity_store","no_rbac","no_auth_method"],
        "allowed_next_action":"create_operator_identity_registry",
        "manual_actions":["provision_operator_ids","configure_rbac","set_up_auth"],
        "no_order_created":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_operator_identity":result}
