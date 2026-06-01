import json,os
def build_paper_order_boundary():
    ob={
        "schema_defined":True,
        "fields":["order_id","ticker","side","quantity","price_type","status","created_at"],
        "execution_blocked":True,
        "order_creation_forbidden":True,
        "boundary_rule":"paper order schema defined but creation is FORBIDDEN",
        "risk_gate_required":True,
        "approval_gate_required":True,
        "kill_switch_gate_required":True,
        "readiness_status":"boundary_defined"
    }
    return {"phase107_paper_order_boundary":ob}
