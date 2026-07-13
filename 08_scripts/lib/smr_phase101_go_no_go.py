import json,os
from datetime import datetime
def build_go_no_go(scorecard):
    sc=scorecard.get("phase101_scorecard",{})
    overall=sc.get("overall_readiness","NOT_READY")
    critical=sc.get("critical_blockers",[])
    major=sc.get("major_gaps",[])
    decision="NO_GO" if overall=="NOT_READY" or len(critical)>0 else "CONDITIONAL_GO"
    return {"phase101_go_no_go":{"generated_at":datetime.now().isoformat()[:10],"decision":decision,"go_live_trading":False,"rationale":f"Critical blockers: {len(critical)}. Major gaps: {len(major)}. System is NOT ready for live trading discussion.","critical_blockers":critical,"major_gaps":major,"next_recommendation":"Resolve critical blockers first: risk control, human approval gate, kill switch, backtest.","mock_used":False,"fixture_used":False}}
