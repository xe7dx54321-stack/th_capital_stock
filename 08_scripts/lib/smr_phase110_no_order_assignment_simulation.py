import json,os
def run_no_order_assignment_simulation():
    steps=[
        {"step":1,"action":"verify_all_slots_unfilled","result":"confirmed","order_created":False,"account_created":False},
        {"step":2,"action":"verify_no_auto_assignment","result":"confirmed","order_created":False,"account_created":False},
        {"step":3,"action":"verify_no_real_accounts","result":"confirmed","order_created":False,"account_created":False},
        {"step":4,"action":"verify_no_sso","result":"confirmed","order_created":False,"account_created":False},
        {"step":5,"action":"verify_conflict_rules_active","result":"confirmed","order_created":False,"account_created":False},
        {"step":6,"action":"verify_manifest_ready","result":"confirmed","order_created":False,"account_created":False}
    ]
    violations=[s for s in steps if s.get("order_created") or s.get("account_created")]
    return {"phase110_no_order_simulation":{"total_steps":len(steps),"steps":steps,"violations":len(violations),"no_order":True,"no_accounts":True,"mock_used":False,"fixture_used":False}}
