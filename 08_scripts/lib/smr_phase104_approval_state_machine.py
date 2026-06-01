import json,os
def build_approval_state_machine():
    states=["pending","operator_approved","supervisor_approved","rejected","expired","revoked"]
    transitions=[
        {"from":"pending","to":"operator_approved","action":"operator_approve"},
        {"from":"operator_approved","to":"supervisor_approved","action":"supervisor_approve"},
        {"from":"pending","to":"rejected","action":"reject"},
        {"from":"operator_approved","to":"rejected","action":"reject"},
        {"from":"pending","to":"expired","action":"expire"},
        {"from":"operator_approved","to":"expired","action":"expire"},
        {"from":"supervisor_approved","to":"revoked","action":"revoke"},
        {"from":"operator_approved","to":"revoked","action":"revoke"}
    ]
    return {"phase104_approval_state_machine":{"states":states,"total_transitions":len(transitions),"transitions":transitions,"two_step_enforced":True,"mock_used":False,"fixture_used":False}}
