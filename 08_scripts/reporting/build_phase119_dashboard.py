import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase119_gap_inventory import build_gap_inventory
from smr_phase119_improvement_board import build_improvement_board
from smr_phase119_cannot_conclude_guard import run_improvement_guard
from smr_phase119_backlog_update import build_backlog_update
def main():
    gaps=build_gap_inventory();board=build_improvement_board();guard=run_improvement_guard();bl=build_backlog_update()
    summary={"phase":"phase119","total_gaps":gaps["phase119_gap_inventory"]["total"],"critical":gaps["phase119_gap_inventory"]["critical"],"improvement_board":board["phase119_improvement_board"]["section_counts"],"guard":guard["phase119_guard"]["overall"],"violations":guard["phase119_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase119_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
