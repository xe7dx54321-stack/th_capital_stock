import json,os
def run_integration_quality_gate(bp,rs,ns,gc,dc,bl,sim):
    gates=[
        {"gate":"blocker_propagation","status":"pass" if bp["phase106_blocker_propagation_checker"]["propagation_healthy"] else "fail"},
        {"gate":"readiness_status","status":"pass" if rs["phase106_readiness_status_consistency"]["all_consistent"] else "fail"},
        {"gate":"no_order_safety","status":"pass" if ns["phase106_no_order_safety_consistency"]["safety_boundary_intact"] else "fail"},
        {"gate":"guard_consistency","status":"pass" if gc["phase106_guard_consistency"]["all_guards_consistent"] else "fail"},
        {"gate":"dashboard_consistency","status":"pass" if dc["phase106_dashboard_consistency"]["all_dashboards_consistent"] else "fail"},
        {"gate":"backlog_consistency","status":"pass" if bl["phase106_backlog_consistency"]["all_backlogs_consistent"] else "fail"},
        {"gate":"cross_gate_simulation","status":"pass" if sim["phase106_cross_gate_simulation"]["all_scenarios_pass"] else "fail"}
    ]
    all_pass=all(g["status"]=="pass" for g in gates)
    return {"phase106_integration_quality_gate":{"overall":"pass" if all_pass else "fail","gates":gates,"total":len(gates),"passed":sum(1 for g in gates if g["status"]=="pass"),"mock_used":False,"fixture_used":False}}
