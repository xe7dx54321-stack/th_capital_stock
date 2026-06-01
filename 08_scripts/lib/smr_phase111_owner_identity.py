def build_owner_identity():
    return {"phase111_owner_identity":{
        "owner_mode":"single_personal_user",
        "owner_identity_set":True,
        "owner_is_sole_user":True,
        "multi_user_not_needed":True,
        "operator_role":"replaced_by_owner",
        "reviewer_role":"replaced_by_owner_review",
        "approver_role":"replaced_by_owner_confirmation",
        "supervisor_role":"not_required",
        "kill_switch_operator_role":"replaced_by_owner_safety_pause",
        "identity_conflicts":0,
        "same_person_conflicts":0,
        "mock_used":False,
        "fixture_used":False
    }}
