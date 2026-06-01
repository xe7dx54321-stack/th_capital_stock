import json,os
from datetime import datetime
def build_backlog_update():
    backlog={
        "generated_at":datetime.now().isoformat(),
        "phase101_blockers":{
            "risk_control_missing":"partially_addressed (Phase103)",
            "human_approval_missing":"partially_addressed (Phase104)",
            "kill_switch_missing":"partially_addressed (Phase105)",
            "backtest_missing":"addressed (Phase102)"
        },
        "phase105_status":{
            "kill_switch_readiness":"partial_ready",
            "critical_remaining":["rollback_procedure_untested","escalation_contacts_missing","snapshot_not_automated"],
            "phase101_all_blockers_addressed":True,
            "next_phase_suggestion":"phase106_integration_test_or_phase107_paper_trading_boundary"
        },
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_backlog_update":backlog}
