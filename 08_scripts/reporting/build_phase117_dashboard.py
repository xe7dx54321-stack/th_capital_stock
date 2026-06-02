import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase117_config import load_config
from smr_phase117_master_board import build_master_board
from smr_phase117_cannot_conclude_guard import run_master_guard
from smr_phase117_backlog_update import build_backlog_update
def main():
    cfg=load_config();board=build_master_board();guard=run_master_guard();bl=build_backlog_update()
    summary={"phase":"phase117","research_only":True,"modules":cfg["modules"],"total_tickers":board["phase117_master_board"]["total"],"sections":board["phase117_master_board"]["section_counts"],"guard":guard["phase117_guard"]["overall"],"violations":guard["phase117_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase117_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
