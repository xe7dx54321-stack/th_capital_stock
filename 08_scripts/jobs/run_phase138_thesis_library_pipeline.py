import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase138_thesis_entity_registry import build_thesis_entity_registry
from smr_phase138_thesis_status_classifier import build_thesis_status_classifier
from smr_phase138_quality_gate import run_quality_gate
from smr_phase138_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase138_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 te=build_thesis_entity_registry()
 ts=build_thesis_status_classifier()
 gq=run_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase138_thesis_library_pipeline":{"mode":mode,"tickers_total":8,"theses_registered":te["phase138_thesis_entity_registry"]["total"],"thesis_summary":ts["phase138_thesis_status_classifier"]["summary"],"quality_gate":gq["phase138_quality_gate"],"guard":cg["phase138_cannot_conclude_guard"],"backlog":bl["phase138_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
