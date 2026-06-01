import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase102_config import load_config
from smr_phase102_historical_db_integrity import check_historical_db_integrity
from smr_phase102_historical_coverage import check_historical_coverage
from smr_phase102_replay_period_registry import build_replay_registry
from smr_phase102_backtest_signal_validator import validate_backtest_signals
from smr_phase102_backtest_quality_gate import run_backtest_quality_gate
from smr_phase102_backtest_cannot_conclude_guard import run_backtest_guard
from smr_phase102_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    di=check_historical_db_integrity();steps.append({"name":"db_integrity","status":"ok"})
    cv=check_historical_coverage();steps.append({"name":"coverage","status":"ok","detail":f"coverage={cv['phase102_historical_coverage']['coverage_pct']}%"})
    rp=build_replay_registry();steps.append({"name":"replay_registry","status":"ok"})
    sv=validate_backtest_signals();steps.append({"name":"signal_validator","status":"ok","detail":f"metrics={sv['phase102_signal_validator']['total_metrics_available']}"})
    gate=run_backtest_quality_gate(di,cv,sv);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase102_quality_gate"]["overall"]})
    guard=run_backtest_guard();steps.append({"name":"guard","status":"ok","detail":f"pnl_backtest_forbidden_reminder=True"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase102_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"pnl_backtest_allowed":False,
            "db_integrity_ok":di["phase102_db_integrity"]["integrity_ok"],
            "coverage_pct":cv["phase102_historical_coverage"]["coverage_pct"],
            "replay_periods":rp["phase102_replay_registry"]["total_periods"],
            "signal_metrics_available":sv["phase102_signal_validator"]["total_metrics_available"],
            "pnl_backtest_attempted":False,
            "quality_gate":gate["phase102_quality_gate"]["overall"],
            "guard":guard["phase102_guard"]["overall"],
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
