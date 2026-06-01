import json,os
from datetime import datetime
def build_backlog_update():
    backlog={
        "generated_at":datetime.now().isoformat(),
        "phase101_blockers":{
            "risk_control_missing":"partially_addressed (Phase103)",
            "human_approval_missing":"partially_addressed (Phase104)",
            "kill_switch_missing":"unresolved",
            "backtest_missing":"addressed (Phase102)"
        },
        "phase104_status":{
            "human_approval_readiness":"partial_ready",
            "critical_remaining":["operator_identity_not_ready","rbac_not_configured"],
            "next_phase_suggestion":"phase105_kill_switch_readiness"
        },
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_backlog_update":backlog}
