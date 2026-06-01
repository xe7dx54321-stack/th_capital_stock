import json,os
def build_assignment_input_template():
    template={
        "template_version":"v1",
        "instructions":"assign_real_person_ids_to_roles_below",
        "contains_no_real_personal_info":True,
        "slots":[
            {"slot":"operator_1","role":"operator","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"},
            {"slot":"reviewer_1","role":"reviewer","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"},
            {"slot":"approver_1","role":"approver","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"},
            {"slot":"approver_2","role":"approver","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"},
            {"slot":"supervisor_1","role":"supervisor","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"},
            {"slot":"kill_switch_op_1","role":"kill_switch_operator","operator_id":"[TO_BE_FILLED_BY_HUMAN]","display_name":"[TO_BE_FILLED]"}
        ]
    }
    return {"phase110_assignment_input_template":{"template":template,"all_slots_unfilled":True,"real_personal_info":False,"mock_used":False,"fixture_used":False}}
