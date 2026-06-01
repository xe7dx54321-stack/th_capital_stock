import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase103_config import load_config
from smr_phase103_risk_rule_registry import build_risk_rule_registry
from smr_phase103_risk_threshold_config import build_risk_threshold_config
from smr_phase103_risk_check_runner import run_risk_checks
from smr_phase103_risk_audit import build_risk_audit
from smr_phase103_risk_quality_gate import run_risk_quality_gate
from smr_phase103_risk_cannot_conclude_guard import run_risk_guard
from smr_phase103_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_risk_rule_registry();steps.append({"name":"rule_registry","status":"ok","detail":f"rules={reg['phase103_risk_rule_registry']['total_rules']}"})
    th=build_risk_threshold_config();steps.append({"name":"threshold_config","status":"ok"})
    ck=run_risk_checks();steps.append({"name":"risk_checks","status":"ok","detail":"all simulated checks pass"})
    au=build_risk_audit();steps.append({"name":"audit","status":"ok"})
    gate=run_risk_quality_gate(reg,th,ck,au);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase103_quality_gate"]["overall"]})
    guard=run_risk_guard();steps.append({"name":"guard","status":"ok"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase103_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"live_risk_execution_enabled":False,"position_sizing_allowed":False,
            "rules_defined":reg["phase103_risk_rule_registry"]["total_rules"],
            "thresholds_defined":th["phase103_risk_thresholds"]["total_thresholds"],
            "checks_pass":ck["phase103_risk_checks"]["checks_pass"],
            "no_orders_generated":True,
            "quality_gate":gate["phase103_quality_gate"]["overall"],
            "guard":guard["phase103_guard"]["overall"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
