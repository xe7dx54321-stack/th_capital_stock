import json,os
def build_assignment_validation_rules():
    rules=[
        {"rule_id":"avr01","rule":"no_empty_slot","description":"all assignment slots must be filled","severity":"critical"},
        {"rule_id":"avr02","rule":"no_duplicate_person_per_constraint","description":"same person cannot fill roles that are forbidden to overlap","severity":"critical"},
        {"rule_id":"avr03","rule":"min_persons_per_role","description":"each role must meet minimum person count","severity":"critical"},
        {"rule_id":"avr04","rule":"no_system_auto_assign","description":"all assignments must be manual","severity":"critical"},
        {"rule_id":"avr05","rule":"approver_min_two_persons","description":"approver role must have at least 2 distinct persons","severity":"critical"}
    ]
    return {"phase110_assignment_validation_rules":{"total_rules":len(rules),"rules":rules,"auto_assignment_blocked":True,"mock_used":False,"fixture_used":False}}
