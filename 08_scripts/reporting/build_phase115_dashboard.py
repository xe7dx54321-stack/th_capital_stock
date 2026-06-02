import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase115_config import load_config
from smr_phase115_category_board import build_category_board
from smr_phase115_cannot_conclude_guard import run_candidate_board_guard
from smr_phase115_backlog_update import build_backlog_update
def main():
    cfg=load_config();board=build_category_board();guard=run_candidate_board_guard();bl=build_backlog_update()
    b=board["phase115_category_board"]
    summary={"phase":"phase115","research_only":cfg["research_only"],"trade_recommendation_allowed":cfg["trade_recommendation_allowed"],"sections":b["section_counts"],"guard":guard["phase115_guard"]["overall"],"violations":guard["phase115_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase115_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
