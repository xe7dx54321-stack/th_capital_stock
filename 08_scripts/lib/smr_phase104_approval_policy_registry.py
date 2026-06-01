import json,os
def build_approval_policy_registry():
    policies=[
        {"policy_id":"ap01","name":"two_step_approval","description":"all actions require operator + supervisor","status":"defined","enforcement":"required"},
        {"policy_id":"ap02","name":"approval_expiration","description":"approvals expire after 24 hours","status":"defined","enforcement":"required"},
        {"policy_id":"ap03","name":"approval_revocation","description":"approvals can be revoked within 72 hours","status":"defined","enforcement":"required"},
        {"policy_id":"ap04","name":"operator_identity","description":"operator must be identified and authorized","status":"defined","enforcement":"required"},
        {"policy_id":"ap05","name":"audit_logging","description":"all approval actions must be logged","status":"defined","enforcement":"required"},
        {"policy_id":"ap06","name":"manual_override","description":"manual override requires supervisor","status":"defined","enforcement":"required"},
        {"policy_id":"ap07","name":"no_auto_approval","description":"no action can be auto-approved without human","status":"defined","enforcement":"required"},
        {"policy_id":"ap08","name":"order_creation_locked","description":"approval does not create orders","status":"defined","enforcement":"required"},
        {"policy_id":"ap09","name":"trade_execution_locked","description":"approval does not execute trades","status":"defined","enforcement":"required"}
    ]
    return {"phase104_approval_policy_registry":{"total_policies":len(policies),"policies":policies,"mock_used":False,"fixture_used":False}}
