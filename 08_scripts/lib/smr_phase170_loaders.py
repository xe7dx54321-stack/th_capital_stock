def load_phase169b_context():
    return {"phase169b_context":{"expectations_all_match":True,"example_coverage":"pass","valid_examples":5,"invalid_examples":7,"mock_used":False,"fixture_used":False}}
def load_phase168_context():
    return {"phase168_context":{"simulation_only":True,"real_activation_not_executed":True,"watch_core_updated":False,"mock_used":False,"fixture_used":False}}
def try_read_owner_input():
    import json, os
    p = "09_runbooks/generated/phase168_owner_decision_manual_submission/owner_decision_input.json"
    if not os.path.exists(p): return None
    try:
        with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
    except: return None
