import json,os
def build_permission_matrix():
    matrix={
        "permissions":{
            "create_paper_order":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "create_paper_trade":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "calculate_paper_pnl":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "create_position_sizing":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "output_target_price":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "connect_broker":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False},
            "enable_live_trading":{"operator":False,"reviewer":False,"approver":False,"supervisor":False,"kill_switch_operator":False}
        },
        "all_execution_permissions_disabled":True,
        "readiness_status":"ready"
    }
    return {"phase109_permission_matrix":{"matrix":matrix,"mock_used":False,"fixture_used":False}}
