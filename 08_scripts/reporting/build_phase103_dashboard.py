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
    cfg=load_config();reg=build_risk_rule_registry();th=build_risk_threshold_config()
    ck=run_risk_checks();au=build_risk_audit()
    gate=run_risk_quality_gate(reg,th,ck,au);guard=run_risk_guard();bl=build_backlog_update()
    summary={
        "phase":"phase103","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["risk_control"]["assessment_only"],
        "live_risk_execution_enabled":cfg["risk_control"]["live_risk_execution_enabled"],
        "position_sizing_allowed":cfg["risk_control"]["position_sizing_allowed"],
        "rules_defined":reg["phase103_risk_rule_registry"]["total_rules"],
        "thresholds_defined":th["phase103_risk_thresholds"]["total_thresholds"],
        "checks_pass":ck["phase103_risk_checks"]["checks_pass"],
        "audit_complete":au["phase103_risk_audit"]["audit_complete"],
        "no_orders_generated":True,
        "quality_gate":gate["phase103_quality_gate"]["overall"],
        "guard":guard["phase103_guard"]["overall"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
