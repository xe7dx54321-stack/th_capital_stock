def build_rollback_plan():
    return {"phase157_rollback_plan":{"rollback_available":True,"rollback_steps":["revert_candidate_to_pending","clear_agent_task_queue","remove_from_simulation_plan"],"undo_plan":"If owner changes mind, all simulations can be discarded. No permanent changes made.","no_permanent_changes":True,"mock_used":False,"fixture_used":False}}
