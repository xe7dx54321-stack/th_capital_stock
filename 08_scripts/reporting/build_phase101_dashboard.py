import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase101_config import load_config
from smr_phase101_phase100_baseline import capture_phase100_baseline
from smr_phase101_scorecard import build_scorecard
from smr_phase101_go_no_go import build_go_no_go
def main():
    cfg=load_config();bl=capture_phase100_baseline();sc=build_scorecard();gg=build_go_no_go(sc)
    summary={
        "phase":"phase101","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["assessment"]["assessment_only"],
        "live_trading_enabled":cfg["assessment"]["live_trading_enabled"],
        "broker_integration_allowed":cfg["assessment"]["broker_integration_allowed"],
        "order_creation_allowed":cfg["assessment"]["order_creation_allowed"],
        "phase100_status":bl["phase101_baseline"]["production_status"],
        "domains_assessed":12,
        "domains_ready":sc["phase101_scorecard"]["domains_ready"],
        "domains_not_ready":sc["phase101_scorecard"]["domains_not_ready"],
        "overall_score_pct":sc["phase101_scorecard"]["score_pct"],
        "overall_readiness":sc["phase101_scorecard"]["overall_readiness"],
        "go_no_go":gg["phase101_go_no_go"]["decision"],
        "critical_blockers":sc["phase101_scorecard"]["critical_blockers"],
        "go_live_trading":False,
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "mock_used":False,"fixture_used":False,"raw_saved":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
