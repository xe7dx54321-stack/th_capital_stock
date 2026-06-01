import json,os
def build_manual_override():
    result={
        "override_enabled":False,
        "requires_supervisor":True,
        "requires_justification":True,
        "requires_audit":True,
        "override_scenarios":["emergency_stop","system_malfunction","false_positive_blocker","exceptional_market_condition"],
        "readiness_status":"partial_ready",
        "blockers":["no_operator_identity","no_supervisor_identity","no_override_justification_template"],
        "allowed_next_action":"define_override_justification_template",
        "no_order_created":True,
        "no_trade_created":True,
        "no_position_sizing":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_manual_override":result}
