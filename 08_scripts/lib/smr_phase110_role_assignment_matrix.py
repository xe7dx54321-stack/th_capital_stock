import json,os
def build_role_assignment_matrix():
    required_roles=[
        {"role":"operator","min_persons":1,"assigned_count":0,"can_overlap_with":[],"status":"unassigned"},
        {"role":"reviewer","min_persons":1,"assigned_count":0,"can_overlap_with":[],"status":"unassigned"},
        {"role":"approver","min_persons":2,"assigned_count":0,"can_overlap_with":[],"status":"unassigned"},
        {"role":"supervisor","min_persons":1,"assigned_count":0,"can_overlap_with":[],"status":"unassigned"},
        {"role":"kill_switch_operator","min_persons":1,"assigned_count":0,"can_overlap_with":[],"status":"unassigned"}
    ]
    return {"phase110_role_assignment_matrix":{"required_roles":len(required_roles),"total_persons_needed":6,"roles":required_roles,"manual_assignment_required":True,"auto_assignment_allowed":False,"mock_used":False,"fixture_used":False}}
