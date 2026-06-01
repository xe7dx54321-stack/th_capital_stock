import json,os
def build_paper_intent_boundary():
    ib={
        "schema_defined":True,
        "fields":["intent_id","ticker","intent_type","reason","evidence_ref","created_at"],
        "execution_blocked":True,
        "cannot_create_order":True,
        "boundary_rule":"paper intent is tracking-only, never becomes order",
        "risk_gate_required":True,
        "approval_gate_required":True,
        "readiness_status":"boundary_defined"
    }
    return {"phase107_paper_intent_boundary":ib}
