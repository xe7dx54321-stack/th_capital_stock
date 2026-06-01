import json,os
def build_operator_identity_schema():
    schema={
        "operator_id":"required, string, unique",
        "display_name":"required, string",
        "role":"required, enum operator roles",
        "status":"required, enum: [active, inactive, suspended]",
        "created_at":"required, iso8601",
        "last_active":"optional, iso8601",
        "auth_method":"not_provisioned",
        "permissions":"derived from role",
        "account_created":False
    }
    return {"phase109_operator_identity_schema":{"schema":schema,"readiness_status":"ready","account_created":0,"sso_connected":0,"password_saved":0,"mock_used":False,"fixture_used":False}}
