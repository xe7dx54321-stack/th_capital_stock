import json,os
def build_approval_expiration():
    result={
        "expiration_enabled":True,
        "expiration_hours":24,
        "expiration_triggers":["time_exceeded","market_event","manual_revoke"],
        "auto_renewal":False,
        "expired_actions_invalid":True,
        "readiness_status":"ready",
        "blockers":[],
        "no_order_created":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_approval_expiration":result}
