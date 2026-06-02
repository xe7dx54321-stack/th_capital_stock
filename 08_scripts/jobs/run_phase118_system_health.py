import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase118_config import load_config
from smr_phase118_domain_registry import build_domain_registry
from smr_phase117_health_checker import check_master_runner_health
from smr_phase118_module_availability import check_module_availability
from smr_phase118_artifact_integrity import check_artifact_integrity
from smr_phase118_data_freshness import check_data_freshness
from smr_phase118_blocker_visibility import check_blocker_visibility
from smr_phase118_generated_path_checker import check_generated_paths
from smr_phase118_latency_monitor import check_latency
from smr_phase118_failure_diagnostics import build_failure_diagnostics
from smr_phase118_degraded_normalizer import build_degraded_normalizer
from smr_phase118_recovery_builder import build_recovery_recommendations
from smr_phase118_reliability_scorecard import build_reliability_scorecard
from smr_phase118_health_board import build_health_board
from smr_phase118_health_history import build_health_history_writer
from smr_phase118_cannot_conclude_guard import run_health_guard
from smr_phase118_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    mh=check_master_runner_health();steps.append({"name":"master_health","status":"ok","detail":f"healthy={mh['phase118_master_health']['master_healthy']}"})
    ma=check_module_availability();steps.append({"name":"module_availability","status":"ok","detail":f"available={ma['phase118_module_availability']['all_available']}"})
    ai=check_artifact_integrity();steps.append({"name":"artifact_integrity","status":"ok","detail":f"ok={ai['phase118_artifact_integrity']['all_ok']}"})
    df=check_data_freshness();steps.append({"name":"data_freshness","status":"ok"})
    bv=check_blocker_visibility();steps.append({"name":"blocker_visibility","status":"ok","detail":f"visible={bv['phase118_blocker_visibility']['all_visible']}"})
    gp=check_generated_paths();steps.append({"name":"generated_paths","status":"ok"})
    lt=check_latency();steps.append({"name":"latency","status":"ok","detail":f"ms={lt['phase118_latency_monitor']['total_estimated_ms']}"})
    fd=build_failure_diagnostics();steps.append({"name":"failure_diagnostics","status":"ok"})
    dn=build_degraded_normalizer();steps.append({"name":"degraded_normalizer","status":"ok"})
    rc=build_recovery_recommendations();steps.append({"name":"recovery","status":"ok"})
    sc=build_reliability_scorecard();steps.append({"name":"scorecard","status":"ok","detail":f"score={sc['phase118_reliability_scorecard']['overall_score']}"})
    board=build_health_board();steps.append({"name":"health_board","status":"ok"})
    hw=build_health_history_writer();steps.append({"name":"history_writer","status":"ok"})
    guard=run_health_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase118_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase118_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"master_healthy":mh["phase118_master_health"]["master_healthy"],"modules_available":ma["phase118_module_availability"]["all_available"],"artifact_integrity":ai["phase118_artifact_integrity"]["all_ok"],"blockers_visible":bv["phase118_blocker_visibility"]["all_visible"],"reliability_score":sc["phase118_reliability_scorecard"]["overall_score"],"above_threshold":sc["phase118_reliability_scorecard"]["above_threshold"],"guard":guard["phase118_guard"]["overall"],"violations":guard["phase118_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase118_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
