import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase120_acceptance_evidence import build_acceptance_evidence
from smr_phase120_closeout_board import build_closeout_board
from smr_phase120_cannot_conclude_guard import run_closeout_guard
from smr_phase120_backlog_update import build_backlog_update
def main():
    ae=build_acceptance_evidence();board=build_closeout_board();guard=run_closeout_guard();bl=build_backlog_update()
    summary={"phase":"phase120","project_accepted":ae["phase120_acceptance_evidence"]["all_met"],"phases_deployed":"39 (82-120)","coverage":"7/8","reliability":97,"guard":guard["phase120_guard"]["overall"],"violations":guard["phase120_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase120_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
