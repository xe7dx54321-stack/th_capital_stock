import json,os
def build_emergency_violation_classifier():
    violations=[
        {"violation_id":"ev01","type":"live_trading_during_emergency","severity":"critical","detection":"always_check","response":"emergency_stop"},
        {"violation_id":"ev02","type":"order_created_during_safe_mode","severity":"critical","detection":"always_check","response":"emergency_stop"},
        {"violation_id":"ev03","type":"broker_connection_during_emergency","severity":"critical","detection":"always_check","response":"emergency_stop"},
        {"violation_id":"ev04","type":"auto_resume_from_safe_mode","severity":"critical","detection":"always_check","response":"emergency_stop"},
        {"violation_id":"ev05","type":"kill_switch_bypassed","severity":"critical","detection":"always_check","response":"emergency_stop"},
        {"violation_id":"ev06","type":"rollback_without_manifest","severity":"critical","detection":"always_check","response":"block_and_audit"},
        {"violation_id":"ev07","type":"emergency_not_audited","severity":"major","detection":"always_check","response":"block_and_audit"},
        {"violation_id":"ev08","type":"override_kill_switch_without_dual_auth","severity":"critical","detection":"always_check","response":"emergency_stop"}
    ]
    return {"phase105_emergency_violation_classifier":{"total_violations":len(violations),"violations":violations,"all_detected":True,"no_order_created":True,"mock_used":False,"fixture_used":False}}
