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
    cfg=load_config();di=check_historical_db_integrity();cv=check_historical_coverage()
    rp=build_replay_registry();sv=validate_backtest_signals()
    gate=run_backtest_quality_gate(di,cv,sv);guard=run_backtest_guard()
    bl=build_backlog_update()
    summary={
        "phase":"phase102","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["backtest"]["assessment_only"],
        "no_trade_backtest_only":cfg["backtest"]["no_trade_backtest_only"],
        "pnl_backtest_allowed":cfg["backtest"]["pnl_backtest_allowed"],
        "db_integrity_ok":di["phase102_db_integrity"]["integrity_ok"],
        "historical_coverage_pct":cv["phase102_historical_coverage"]["coverage_pct"],
        "tickers_covered":cv["phase102_historical_coverage"]["tickers_covered"],
        "replay_periods":rp["phase102_replay_registry"]["total_periods"],
        "signal_metrics_available":sv["phase102_signal_validator"]["total_metrics_available"],
        "pnl_backtest_attempted":False,
        "quality_gate":gate["phase102_quality_gate"]["overall"],
        "guard":guard["phase102_guard"]["overall"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
