import json,os
def build_approval_role_binding():
    return {"phase109_approval_role_binding":{"two_step_binding":{"step1":"operator or reviewer","step2":"approver or supervisor"},"same_person_forbidden":True,"binding_readiness":"ready","provisioned":False,"allowed_next_action":"assign_real_operators_to_roles","mock_used":False,"fixture_used":False}}
