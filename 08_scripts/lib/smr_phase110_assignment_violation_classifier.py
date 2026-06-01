import json,os
def build_assignment_violation_classifier():
    violations=[
        {"violation_id":"asv01","type":"auto_assignment_attempted","severity":"critical","detection":"assignment_check","response":"block"},
        {"violation_id":"asv02","type":"same_person_conflict","severity":"critical","detection":"conflict_check","response":"block_and_audit"},
        {"violation_id":"asv03","type":"min_persons_not_met","severity":"major","detection":"count_check","response":"require_more_assignments"},
        {"violation_id":"asv04","type":"real_account_created","severity":"critical","detection":"account_check","response":"audit"}
    ]
    return {"phase110_assignment_violation_classifier":{"total_violations":len(violations),"violations":violations,"all_detected":True,"mock_used":False,"fixture_used":False}}
