import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase139_phase138_thesis_loader import load_phase138_thesis
from smr_phase139_run_schedule_profile import build_run_schedule_profile
from smr_phase139_delivery_quality_gate import run_delivery_quality_gate
from smr_phase139_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase139_backlog_update import build_backlog_update
def main():
 sp=build_run_schedule_profile()
 gq=run_delivery_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase139_dashboard":{"phase":"phase139","strategy":"scheduled_local_delivery","research_only":True,"schedule":sp["phase139_run_schedule_profile"]["schedule"],"quality_gate":gq["phase139_delivery_quality_gate"],"guard":cg["phase139_cannot_conclude_guard"],"backlog":bl["phase139_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
