import json,os
def build_disable_live_mode():
    result={
        "live_mode_disabled":True,
        "live_trading_disabled":True,
        "broker_connection_disabled":True,
        "order_creation_disabled":True,
        "trade_execution_disabled":True,
        "position_sizing_disabled":True,
        "read_only_operations_allowed":True,
        "disable_triggers":["system_anomaly","data_corruption","risk_breach","unauthorized_access","kill_switch_manual"],
        "reactivation_requires":"dual_authorization",
        "auto_reactivation":False,
        "readiness_status":"ready",
        "no_order_created":True,"no_trade_created":True,"no_broker_action":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_disable_live_mode":result}
