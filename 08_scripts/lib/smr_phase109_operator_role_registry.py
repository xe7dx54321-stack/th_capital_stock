import json,os
def build_operator_role_registry():
    roles=[
        {"role_id":"r01","name":"operator","permissions":["read_config","read_data","read_signals","view_dashboard","generate_report"],"can_create_order":False,"can_approve":False,"can_override":False,"can_kill_switch":False},
        {"role_id":"r02","name":"reviewer","permissions":["read_config","read_data","read_signals","view_dashboard","review_checklist"],"can_create_order":False,"can_approve":False,"can_override":False,"can_kill_switch":False},
        {"role_id":"r03","name":"approver","permissions":["approve_request","reject_request","view_audit_log"],"can_create_order":False,"can_approve":True,"can_override":False,"can_kill_switch":False},
        {"role_id":"r04","name":"supervisor","permissions":["override_approval","revoke_approval","approve_resume","view_audit_log"],"can_create_order":False,"can_approve":True,"can_override":True,"can_kill_switch":False},
        {"role_id":"r05","name":"kill_switch_operator","permissions":["trigger_safe_mode","trigger_emergency_stop","approve_resume","view_audit_log"],"can_create_order":False,"can_approve":False,"can_override":False,"can_kill_switch":True}
    ]
    return {"phase109_operator_role_registry":{"total_roles":len(roles),"roles":roles,"all_order_creation_disabled":True,"mock_used":False,"fixture_used":False}}
