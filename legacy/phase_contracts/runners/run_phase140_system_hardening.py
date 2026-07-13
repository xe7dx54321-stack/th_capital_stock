import json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))
from smr_phase140_operational_reliability_scorecard import build_operational_reliability_scorecard
from smr_phase140_quality_gate import run_quality_gate
from smr_phase140_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase140_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 sc=build_operational_reliability_scorecard()
 gq=run_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase140_system_hardening_pipeline":{"mode":mode,"tickers_total":8,"scorecard":sc["phase140_operational_reliability_scorecard"]["scorecard"],"quality_gate":gq["phase140_quality_gate"],"guard":cg["phase140_cannot_conclude_guard"],"backlog":bl["phase140_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
