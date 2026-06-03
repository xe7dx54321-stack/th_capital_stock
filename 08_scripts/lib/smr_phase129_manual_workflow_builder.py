import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe

def build_manual_workflow(skip_network=False):
    results=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]["results"]
    manual=[r for r in results if r.get("resolution")=="manual_source_workflow_required"]
    workflows=[]
    for m in manual:
        wf={"source_id":m["source_id"],"workflow_steps":["1.search_finviz_or_marketwatch_for_earnings_news","2.check_yfinance_for_earnings_dates","3.manually_search_Seeking_Alpha_free_tier_for_transcript","4.record_key_guidance_points_in_decision_journal","5.mark_as_manual_observation_not_automated_signal"],"estimated_time_per_ticker":"15-30 minutes","frequency":"quarterly_per_earnings","automation_feasible":False,"owner_action_required":True}
        workflows.append(wf)
    return {"phase129_manual_workflow_builder":{"total":len(workflows),"all_require_owner_action":True,"workflows":workflows,"mock_used":False,"fixture_used":False}}
