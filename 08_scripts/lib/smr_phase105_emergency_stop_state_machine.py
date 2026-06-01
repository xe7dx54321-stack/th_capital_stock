import json,os
def build_emergency_stop_state_machine():
    states=["normal","safe_mode","emergency_stop","rollback_in_progress","rollback_complete","resume_pending"]
    transitions=[
        {"from":"normal","to":"safe_mode","action":"trigger_safe_mode","severity":"warning"},
        {"from":"safe_mode","to":"emergency_stop","action":"trigger_emergency_stop","severity":"critical"},
        {"from":"normal","to":"emergency_stop","action":"trigger_immediate_stop","severity":"critical"},
        {"from":"emergency_stop","to":"rollback_in_progress","action":"initiate_rollback","severity":"critical"},
        {"from":"rollback_in_progress","to":"rollback_complete","action":"verify_rollback","severity":"critical"},
        {"from":"safe_mode","to":"resume_pending","action":"request_resume","severity":"warning"},
        {"from":"resume_pending","to":"normal","action":"approve_resume","severity":"normal"},
        {"from":"emergency_stop","to":"rollback_complete","action":"force_rollback","severity":"critical"}
    ]
    return {"phase105_emergency_stop_state_machine":{"states":states,"total_transitions":len(transitions),"transitions":transitions,"auto_resume_disabled":True,"mock_used":False,"fixture_used":False}}
