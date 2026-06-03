import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase131_integration_decision_builder import build_integration_decision
from smr_phase131_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase131_backlog_update import build_backlog_update
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
def main():
 d=build_integration_decision()
 g=run_cannot_conclude_guard()
 b=build_backlog_update()
 w=build_watchlist_coverage_update()
 r={"phase131_dashboard":{"phase":"phase131","strategy":"300394_alternative_source_integration","coverage":w["phase131_watchlist_coverage_update"],"decision":d["phase131_integration_decision_builder"],"guard":g["phase131_cannot_conclude_guard"],"backlog":b["phase131_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
