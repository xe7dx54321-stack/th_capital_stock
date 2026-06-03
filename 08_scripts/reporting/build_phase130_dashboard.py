import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase130_backlog_update import build_backlog_update
from smr_phase130_resolution_decision_report import build_resolution_decision_report
def main():
 gc=build_gap_closeout_report()
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 dc=build_resolution_decision_report()
 r={"phase130_dashboard":{"phase":"phase130","strategy":"300394_cninfo_resolution","ticker":"300394.SZ","blocker_status":gc["phase130_gap_closeout_report"]["blocker_status"],"decision":dc["phase130_resolution_decision_report"]["decision"],"guard":gd["phase130_cannot_conclude_guard"],"backlog":bl["phase130_backlog_update"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
