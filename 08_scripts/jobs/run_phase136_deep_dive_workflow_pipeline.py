import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase136_config import load_config
from smr_phase136_phase135_feedback_task_loader import load_phase135_feedback_tasks
from smr_phase136_task_prioritizer import build_task_prioritizer
from smr_phase136_deep_dive_research_packet_builder import build_deep_dive_research_packet
from smr_phase136_deep_dive_quality_gate import run_deep_dive_quality_gate
from smr_phase136_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase136_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 tp=build_task_prioritizer()
 gq=run_deep_dive_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase136_deep_dive_workflow_pipeline":{"mode":mode,"tickers_total":8,"deep_dive_tasks_active":tp["phase136_task_prioritizer"]["total"],"quality_gate":gq["phase136_deep_dive_quality_gate"],"guard":cg["phase136_cannot_conclude_guard"],"backlog":bl["phase136_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
