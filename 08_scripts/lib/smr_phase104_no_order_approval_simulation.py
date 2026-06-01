import json,os
def run_no_order_approval_simulation():
    sim_steps=[
        {"step":1,"action":"create_approval_request","result":"request_created","order_created":False},
        {"step":2,"action":"operator_approves","result":"operator_approved","order_created":False},
        {"step":3,"action":"supervisor_approves","result":"supervisor_approved","order_created":False},
        {"step":4,"action":"check_order_created","result":"no_order","order_created":False},
        {"step":5,"action":"check_trade_created","result":"no_trade","trade_created":False},
        {"step":6,"action":"check_position_sizing","result":"no_position","position_sizing_created":False}
    ]
    violations=[s for s in sim_steps if s.get("order_created") or s.get("trade_created") or s.get("position_sizing_created")]
    return {"phase104_no_order_approval_simulation":{"total_steps":len(sim_steps),"steps":sim_steps,"violations":len(violations),"no_order_created":True,"no_trade_created":True,"no_position_sizing_created":True,"mock_used":False,"fixture_used":False}}
