import json,os
def build_paper_signal_boundary():
    sb={
        "schema_defined":True,
        "fields":["ticker","signal_type","direction","confidence","evidence_ref","generated_at"],
        "execution_blocked":True,
        "cannot_create_order":True,
        "cannot_trigger_trade":True,
        "boundary_rule":"paper signal is observation-only, never triggers execution",
        "risk_gate_required":True,
        "approval_gate_required":True,
        "readiness_status":"boundary_defined"
    }
    return {"phase107_paper_signal_boundary":sb}
