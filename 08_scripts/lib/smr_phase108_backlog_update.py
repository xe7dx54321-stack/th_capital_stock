import json,os
from datetime import datetime
def build_backlog_update():
    backlog={
        "generated_at":datetime.now().isoformat(),
        "phase108_status":{
            "paper_execution_readiness":"partial_ready",
            "ready_for_paper_execution":False,
            "blockers":["operator_identity","human_approval","risk_control","kill_switch"],
            "paper_order_schema_review":"pass",
            "paper_trade_schema_review":"pass",
            "paper_portfolio_schema_review":"pass",
            "paper_pnl_policy":"partial_ready",
            "paper_sizing_policy":"partial_ready",
            "paper_order_execution_missing":"partially_addressed",
            "paper_trade_execution_missing":"partially_addressed",
            "paper_pnl_policy_missing":"partially_addressed",
            "operator_identity_missing":"still_blocking",
            "next_phase":"phase109_paper_execution_activation_or_phase109_operator_identity_provisioning"
        },
        "mock_used":False,"fixture_used":False
    }
    return {"phase108_backlog_update":backlog}
