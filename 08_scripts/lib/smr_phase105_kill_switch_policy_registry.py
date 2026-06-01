import json,os
def build_kill_switch_policy_registry():
    policies=[
        {"policy_id":"ksp01","name":"disable_live_trading","description":"kill switch immediately disables all live trading","status":"defined","enforcement":"required"},
        {"policy_id":"ksp02","name":"disable_order_creation","description":"kill switch immediately disables all order creation","status":"defined","enforcement":"required"},
        {"policy_id":"ksp03","name":"disable_broker_connection","description":"kill switch immediately isolates broker connections","status":"defined","enforcement":"required"},
        {"policy_id":"ksp04","name":"safe_mode_all_operations","description":"safe mode allows read-only operations only","status":"defined","enforcement":"required"},
        {"policy_id":"ksp05","name":"audit_all_emergency_actions","description":"all emergency actions must be audited","status":"defined","enforcement":"required"},
        {"policy_id":"ksp06","name":"rollback_manifest_required","description":"every emergency action requires rollback manifest","status":"defined","enforcement":"required"},
        {"policy_id":"ksp07","name":"manual_override_requires_dual_auth","description":"manual override of kill switch requires dual authorization","status":"defined","enforcement":"required"},
        {"policy_id":"ksp08","name":"incident_escalation_chain","description":"unresolved incidents escalate through defined chain","status":"defined","enforcement":"required"},
        {"policy_id":"ksp09","name":"no_auto_resume","description":"system cannot auto-resume from safe mode","status":"defined","enforcement":"required"}
    ]
    return {"phase105_kill_switch_policy_registry":{"total_policies":len(policies),"policies":policies,"mock_used":False,"fixture_used":False}}
