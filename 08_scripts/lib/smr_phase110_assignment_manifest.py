import json,os
def build_assignment_manifest():
    manifest={
        "manifest_id":"phase110-manifest-001",
        "roles_to_assign":5,
        "persons_required":6,
        "manual_fill_required":True,
        "auto_fill_disabled":True,
        "real_personal_info_required":False,
        "identity_fields_template":["role","operator_id","display_name","contact","department"],
        "no_real_accounts_created":True,
        "no_sso_connections":True,
        "readiness_status":"ready_for_manual_fill"
    }
    return {"phase110_assignment_manifest":{"manifest":manifest,"mock_used":False,"fixture_used":False}}
