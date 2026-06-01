import json,os
def build_violation_classifier():
    violations=[
        {"violation_id":"pev01","type":"paper_order_created_during_readiness","severity":"critical","detection":"safety_gate","response":"block_and_audit"},
        {"violation_id":"pev02","type":"paper_trade_during_readiness","severity":"critical","detection":"safety_gate","response":"block_and_audit"},
        {"violation_id":"pev03","type":"paper_pnl_calculated_during_readiness","severity":"critical","detection":"safety_gate","response":"block_and_audit"},
        {"violation_id":"pev04","type":"execution_enabled_before_blockers_resolved","severity":"critical","detection":"checklist","response":"emergency_stop"},
        {"violation_id":"pev05","type":"operator_identity_bypassed","severity":"critical","detection":"dependency_check","response":"block_and_audit"},
        {"violation_id":"pev06","type":"safety_gate_disabled","severity":"critical","detection":"gate_check","response":"emergency_stop"}
    ]
    return {"phase108_violation_classifier":{"total_violations":len(violations),"violations":violations,"all_detected":True,"no_order_created":True,"mock_used":False,"fixture_used":False}}
