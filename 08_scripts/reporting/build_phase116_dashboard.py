import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase116_config import load_config
from smr_phase116_research_board import build_research_board
from smr_phase116_cannot_conclude_guard import run_watchlist_guard
from smr_phase116_backlog_update import build_backlog_update
def main():
    cfg=load_config();board=build_research_board();guard=run_watchlist_guard();bl=build_backlog_update()
    b=board["phase116_research_board"]
    summary={"phase":"phase116","research_only":cfg["research_only"],"total_tickers":b["total"],"sections":b["section_counts"],"guard":guard["phase116_guard"]["overall"],"violations":guard["phase116_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase116_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
