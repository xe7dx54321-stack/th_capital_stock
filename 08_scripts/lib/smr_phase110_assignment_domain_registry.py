import json,os
def build_assignment_domain_registry():
    domains=[
        {"domain_id":"as01","name":"operator_assignment_manifest","readiness_status":"ready","assigned":False},
        {"domain_id":"as02","name":"role_assignment_matrix","readiness_status":"ready","assigned":False},
        {"domain_id":"as03","name":"assignment_input_template","readiness_status":"ready","assigned":False},
        {"domain_id":"as04","name":"assignment_validation_rules","readiness_status":"ready","assigned":False},
        {"domain_id":"as05","name":"role_conflict_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as06","name":"same_person_assignment_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as07","name":"dual_control_assignment_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as08","name":"supervisor_assignment_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as09","name":"kill_switch_operator_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as10","name":"approval_chain_assignment_check","readiness_status":"ready","assigned":False},
        {"domain_id":"as11","name":"assignment_audit_log","readiness_status":"ready","assigned":False},
        {"domain_id":"as12","name":"paper_execution_assignment_dependency","readiness_status":"blocked","assigned":False}
    ]
    return {"phase110_assignment_domain_registry":{"total_domains":len(domains),"domains":domains,"all_schema_ready":True,"all_assignments_pending":True,"mock_used":False,"fixture_used":False}}
