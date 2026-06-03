import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase140_operational_reliability_scorecard import build_operational_reliability_scorecard
from smr_phase140_recovery_recommendation_builder import build_recovery_recommendation
from smr_phase140_quality_gate import run_quality_gate
from smr_phase140_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase140_backlog_update import build_backlog_update
def main():
 sc=build_operational_reliability_scorecard()
 rc=build_recovery_recommendation()
 gq=run_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase140_dashboard":{"phase":"phase140","strategy":"system_hardening","research_only":True,"scorecard":sc["phase140_operational_reliability_scorecard"]["scorecard"],"recovery_ready":rc["phase140_recovery_recommendation_builder"]["ready"],"quality_gate":gq["phase140_quality_gate"],"guard":cg["phase140_cannot_conclude_guard"],"backlog":bl["phase140_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
