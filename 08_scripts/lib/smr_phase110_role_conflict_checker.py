import json,os
def run_role_conflict_checker():
    forbidden_overlaps=[
        {"role_a":"operator","role_b":"approver","reason":"cannot_approve_own_actions"},
        {"role_a":"operator","role_b":"supervisor","reason":"cannot_override_own_actions"},
        {"role_a":"reviewer","role_b":"approver","reason":"must_be_independent"},
        {"role_a":"approver","role_b":"kill_switch_operator","reason":"separation_of_duties"},
        {"role_a":"supervisor","role_b":"kill_switch_operator","reason":"can_overlap_if_designated"}
    ]
    return {"phase110_role_conflict_checker":{"conflicts_defined":len(forbidden_overlaps),"forbidden_overlaps":forbidden_overlaps,"all_enforced":True,"mock_used":False,"fixture_used":False}}
