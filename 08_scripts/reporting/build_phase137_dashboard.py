import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase137_phase136_task_loader import load_phase136_tasks
from smr_phase137_evidence_delta_classifier import build_evidence_delta_classifier
from smr_phase137_task_status_closeout_builder import build_task_status_closeout
from smr_phase137_quality_gate import run_quality_gate
from smr_phase137_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase137_backlog_update import build_backlog_update
def main():
 p136=load_phase136_tasks()
 ed=build_evidence_delta_classifier()
 co=build_task_status_closeout()
 gq=run_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase137_dashboard":{"phase":"phase137","strategy":"deep_dive_execution","research_only":True,"tasks_loaded":p136["phase137_phase136_task_loader"]["total"],"evidence_deltas":ed["phase137_evidence_delta_classifier"]["total"],"closeouts":co["phase137_task_status_closeout_builder"]["total"],"quality_gate":gq["phase137_quality_gate"],"guard":cg["phase137_cannot_conclude_guard"],"backlog":bl["phase137_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
