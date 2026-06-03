import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase132_gap_closeout_report import build_gap_closeout_report
from smr_phase132_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase132_backlog_update import build_backlog_update
def main():
 gc=build_gap_closeout_report()
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase132_dashboard":{"phase":"phase132","strategy":"688041_valuation_hardening","coverage_status":"all_8_full_coverage","valuation_gap":gc["phase132_gap_closeout_report"]["overall_resolution"],"guard":gd["phase132_cannot_conclude_guard"],"backlog":bl["phase132_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
