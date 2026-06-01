import json,os
def build_manual_assignment_checklist():
    items=[
        {"item":"operator_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"reviewer_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"approver_1_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"approver_2_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"supervisor_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"kill_switch_operator_assigned","status":"unassigned","required":True,"blocker":True},
        {"item":"no_role_conflict","status":"pending_assignments","required":True,"blocker":True},
        {"item":"no_same_person_conflict","status":"pending_assignments","required":True,"blocker":True}
    ]
    assigned=sum(1 for i in items if i["status"]=="assigned")
    return {"phase110_manual_assignment_checklist":{"total":len(items),"assigned":assigned,"all_assigned":assigned==len(items),"ready_for_paper_execution":False,"manual_action_required":True,"mock_used":False,"fixture_used":False}}
