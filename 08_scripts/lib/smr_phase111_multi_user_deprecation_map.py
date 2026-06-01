def build_multi_user_deprecation_map():
    roles=[
        {"role":"operator","phase110_status":"unassigned","phase111_status":"deprecated_replaced_by_owner","deprecation_reason":"personal_owner_mode_single_user"},
        {"role":"reviewer","phase110_status":"unassigned","phase111_status":"deprecated_replaced_by_owner_review","deprecation_reason":"owner_self_review_in_personal_mode"},
        {"role":"approver_1","phase110_status":"unassigned","phase111_status":"deprecated_replaced_by_owner_confirmation","deprecation_reason":"owner_self_confirmation_in_personal_mode"},
        {"role":"approver_2","phase110_status":"unassigned","phase111_status":"deprecated_not_required","deprecation_reason":"dual_approval_not_needed_for_personal_mode"},
        {"role":"supervisor","phase110_status":"unassigned","phase111_status":"deprecated_not_required","deprecation_reason":"no_external_supervision_in_personal_mode"},
        {"role":"kill_switch_operator","phase110_status":"unassigned","phase111_status":"deprecated_replaced_by_owner_safety_pause","deprecation_reason":"owner_is_safety_controller"}
    ]
    all_deprecated=all(r["phase111_status"].startswith("deprecated") for r in roles)
    return {"phase111_multi_user_deprecation_map":{"total_roles":len(roles),"all_deprecated":all_deprecated,"deprecation_reason":"personal_owner_mode","roles":roles,"multi_user_assignment_no_longer_required":True,"mock_used":False,"fixture_used":False}}
