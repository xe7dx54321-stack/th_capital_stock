import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase118_reliability_scorecard import build_reliability_scorecard
from smr_phase118_health_board import build_health_board
from smr_phase118_cannot_conclude_guard import run_health_guard
from smr_phase118_backlog_update import build_backlog_update
def main():
    sc=build_reliability_scorecard();board=build_health_board();guard=run_health_guard();bl=build_backlog_update()
    summary={"phase":"phase118","reliability_score":sc["phase118_reliability_scorecard"]["overall_score"],"above_threshold":sc["phase118_reliability_scorecard"]["above_threshold"],"health_board":board["phase118_health_board"]["section_counts"],"guard":guard["phase118_guard"]["overall"],"violations":guard["phase118_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase118_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
