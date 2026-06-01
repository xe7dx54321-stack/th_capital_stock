import json,os
def build_cross_gate_dependency_registry():
    deps=[
        {"dep_id":"d01","from_module":"historical_replay","to_module":"risk_control","expectation":"replay coverage gap must propagate to data_quality_risk","check_type":"blocker_propagation","critical":True},
        {"dep_id":"d02","from_module":"historical_replay","to_module":"risk_control","expectation":"replay source blocked must propagate to blocker_risk","check_type":"blocker_propagation","critical":True},
        {"dep_id":"d03","from_module":"risk_control","to_module":"human_approval","expectation":"risk not_ready must block approval design_approved entry","check_type":"gate_blocking","critical":True},
        {"dep_id":"d04","from_module":"risk_control","to_module":"human_approval","expectation":"risk violation must trigger approval risk_review_required","check_type":"gate_blocking","critical":True},
        {"dep_id":"d05","from_module":"human_approval","to_module":"kill_switch","expectation":"approval not_ready must not bypass kill_switch","check_type":"gate_blocking","critical":True},
        {"dep_id":"d06","from_module":"human_approval","to_module":"kill_switch","expectation":"approval partial_ready must be recognized by kill_switch escalation","check_type":"status_awareness","critical":True},
        {"dep_id":"d07","from_module":"kill_switch","to_module":"historical_replay","expectation":"emergency stop state must be visible in replay audit","check_type":"status_awareness","critical":True},
        {"dep_id":"d08","from_module":"risk_control","to_module":"kill_switch","expectation":"risk breach must trigger safe_mode escalation","check_type":"escalation","critical":True},
        {"dep_id":"d09","from_module":"historical_replay","to_module":"human_approval","expectation":"replay trace missing must prevent human_approval readiness upgrade","check_type":"gate_blocking","critical":False}
    ]
    return {"phase106_cross_gate_dependency_registry":{"total_dependencies":len(deps),"dependencies":deps,"all_no_order":True,"mock_used":False,"fixture_used":False}}
