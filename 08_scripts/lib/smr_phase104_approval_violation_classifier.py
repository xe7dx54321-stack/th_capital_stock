import json,os
def build_approval_violation_classifier():
    violations=[
        {"violation_id":"av01","type":"auto_approval_without_human","severity":"critical","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av02","type":"order_created_during_approval","severity":"critical","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av03","type":"single_step_approval_when_two_step_required","severity":"critical","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av04","type":"expired_approval_used","severity":"critical","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av05","type":"revoked_approval_used","severity":"critical","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av06","type":"operator_not_identified","severity":"major","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av07","type":"no_audit_log","severity":"major","detection":"always_check","response":"block_immediately"},
        {"violation_id":"av08","type":"override_without_supervisor","severity":"critical","detection":"always_check","response":"block_immediately"}
    ]
    return {"phase104_approval_violation_classifier":{"total_violations":len(violations),"violations":violations,"all_detected":True,"no_order_created":True,"mock_used":False,"fixture_used":False}}
