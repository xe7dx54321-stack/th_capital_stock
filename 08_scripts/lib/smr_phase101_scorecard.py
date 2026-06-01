import json,os
from datetime import datetime
def build_scorecard():
    domains=[
        {"domain":"data_source","score":6,"max":10,"readiness":"not_ready"},
        {"domain":"hard_data_db","score":7,"max":10,"readiness":"partially_ready"},
        {"domain":"production_monitoring","score":8,"max":10,"readiness":"ready"},
        {"domain":"evidence_signal","score":6,"max":10,"readiness":"not_ready"},
        {"domain":"risk_control","score":0,"max":15,"readiness":"not_ready"},
        {"domain":"paper_live_boundary","score":10,"max":10,"readiness":"ready"},
        {"domain":"human_approval","score":0,"max":10,"readiness":"not_ready"},
        {"domain":"execution_lockdown","score":10,"max":10,"readiness":"ready"},
        {"domain":"audit_log","score":5,"max":10,"readiness":"not_ready"},
        {"domain":"emergency_control","score":0,"max":10,"readiness":"not_ready"},
        {"domain":"compliance_guardrail","score":8,"max":5,"readiness":"ready"},
        {"domain":"system_stability","score":7,"max":5,"readiness":"partially_ready"},
    ]
    total_max=sum(d["max"] for d in domains); total_score=sum(d["score"] for d in domains)
    ready=sum(1 for d in domains if d["readiness"]=="ready")
    not_ready=sum(1 for d in domains if d["readiness"]=="not_ready")
    partial=sum(1 for d in domains if d["readiness"]=="partially_ready")
    return {"phase101_scorecard":{"generated_at":datetime.now().isoformat()[:10],"total_domains":len(domains),"domains_ready":ready,"domains_not_ready":not_ready,"domains_partially_ready":partial,"total_score":total_score,"total_max":total_max,"score_pct":round(total_score/total_max*100,1),"overall_readiness":"NOT_READY","critical_blockers":["risk_control_missing","human_approval_missing","kill_switch_missing","backtest_missing"],"major_gaps":["audit_log_incomplete","data_source_incomplete","evidence_signal_unverified"],"domains":domains,"mock_used":False,"fixture_used":False}}
