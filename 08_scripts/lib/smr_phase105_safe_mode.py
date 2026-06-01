import json,os
def build_safe_mode():
    result={
        "safe_mode_readiness":"ready",
        "allowed_operations":["read_config","read_data","read_signals","read_history","view_dashboard","export_report"],
        "blocked_operations":["create_order","execute_trade","connect_broker","calculate_position","generate_target_price","write_trade"],
        "entry_triggers":["manual_activation","data_anomaly_detected","risk_breach_detected","broker_connection_failure"],
        "exit_requires":"dual_authorization_and_incident_review",
        "auto_exit":False,
        "no_order_created":True,"no_trade_created":True,"no_broker_action":True,"no_position_sizing":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_safe_mode":result}
