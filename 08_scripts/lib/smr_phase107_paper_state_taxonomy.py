import json,os
def build_paper_state_taxonomy():
    states=[
        {"state":"boundary_undefined","description":"paper trading concept not yet defined","current":False,"allowed_transition":"boundary_defined"},
        {"state":"boundary_defined","description":"paper trading boundaries fully specified","current":True,"allowed_transition":"readiness_check_passed"},
        {"state":"readiness_check_passed","description":"all pre-paper checklist items satisfied","current":False,"allowed_transition":"paper_trading_enabled"},
        {"state":"paper_trading_enabled","description":"paper trading execution allowed","current":False,"allowed_transition":"not_reachable_yet"},
        {"state":"paper_execution_paused","description":"paper trading temporarily paused","current":False,"allowed_transition":"paper_trading_enabled"},
        {"state":"paper_execution_terminated","description":"paper trading permanently disabled","current":False,"allowed_transition":"none"}
    ]
    return {"phase107_paper_state_taxonomy":{"total_states":len(states),"current_state":"boundary_defined","current_cannot_execute":True,"paper_execution_reachable":False,"mock_used":False,"fixture_used":False}}
