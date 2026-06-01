import json,os
def build_same_operator_forbidden():
    return {"phase109_same_operator_forbidden":{"rule":"same_operator_cannot_both_request_and_approve","enforced":True,"scope":["paper_order","paper_trade","override","emergency_exit"],"detection":"identity_match_check","readiness_status":"ready","mock_used":False,"fixture_used":False}}
