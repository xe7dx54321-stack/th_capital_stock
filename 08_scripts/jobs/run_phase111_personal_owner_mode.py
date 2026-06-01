import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase111_config import load_config
from smr_phase111_owner_mode_domain_registry import build_owner_mode_domain_registry
from smr_phase111_owner_identity import build_owner_identity
from smr_phase111_owner_confirmation_gate import build_owner_confirmation_gate
from smr_phase111_research_action_taxonomy import build_research_action_taxonomy
from smr_phase111_owner_action_queue import build_owner_action_queue
from smr_phase111_research_risk_gate import build_research_risk_gate
from smr_phase111_research_safety_mode import build_research_safety_mode
from smr_phase111_evidence_first_policy import build_evidence_first_policy
from smr_phase111_multi_user_deprecation_map import build_multi_user_deprecation_map
from smr_phase111_paper_execution_deprecation_map import build_paper_execution_deprecation_map
from smr_phase111_personal_audit_log import build_personal_audit_log
from smr_phase111_personal_dashboard_state import build_personal_dashboard_state
from smr_phase111_owner_mode_migration_report import build_owner_mode_migration_report
from smr_phase111_cannot_conclude_guard import run_owner_mode_cannot_conclude_guard
from smr_phase111_backlog_reframe import build_backlog_reframe
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_owner_mode_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"active={dom['phase111_owner_mode_domain_registry']['active_domains']}"})
    ident=build_owner_identity();steps.append({"name":"owner_identity","status":"ok"})
    gate=build_owner_confirmation_gate();steps.append({"name":"confirmation_gate","status":"ok","detail":f"pass={gate['phase111_owner_confirmation_gate']['all_pass']}"})
    tax=build_research_action_taxonomy();steps.append({"name":"action_taxonomy","status":"ok","detail":f"active_actions={tax['phase111_research_action_taxonomy']['active_actions']}"})
    q=build_owner_action_queue();steps.append({"name":"action_queue","status":"ok","detail":f"queued={q['phase111_owner_action_queue']['queued']}"})
    risk=build_research_risk_gate();steps.append({"name":"risk_gate","status":"ok","detail":f"pass={risk['phase111_research_risk_gate']['all_pass']}"})
    safety=build_research_safety_mode();steps.append({"name":"safety_mode","status":"ok"})
    ev=build_evidence_first_policy();steps.append({"name":"evidence_policy","status":"ok"})
    mu=build_multi_user_deprecation_map();steps.append({"name":"multi_user_deprecation","status":"ok","detail":f"deprecated={mu['phase111_multi_user_deprecation_map']['all_deprecated']}"})
    pe=build_paper_execution_deprecation_map();steps.append({"name":"paper_exec_deprecation","status":"ok","detail":f"disabled={pe['phase111_paper_execution_deprecation_map']['all_permanently_disabled']}"})
    audit=build_personal_audit_log();steps.append({"name":"audit_log","status":"ok"})
    ds=build_personal_dashboard_state();steps.append({"name":"dashboard_state","status":"ok"})
    mig=build_owner_mode_migration_report();steps.append({"name":"migration_report","status":"ok"})
    guard=run_owner_mode_cannot_conclude_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase111_guard"]["overall"]})
    bl=build_backlog_reframe();steps.append({"name":"backlog_reframe","status":"ok"})
    out={"phase111_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"personal_use_system":True,"owner_mode_enabled":True,"multi_user_assignment_required":False,"owner_confirmation_required":True,"research_support_mode":True,"opportunity_discovery_mode":True,"watchlist_tracking_mode":True,"team_approval_required":False,"supervisor_required":False,"paper_execution_enabled":False,"live_trading_enabled":False,"broker_integration_allowed":False,"active_domains":dom["phase111_owner_mode_domain_registry"]["active_domains"],"guard":guard["phase111_guard"]["overall"],"violations":guard["phase111_guard"]["violations"],"next_phase":"phase112_opportunity_radar_v1","blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"account_created":0,"sso_connected":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
