# Phase176 coverage state reconciliation runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase176_reconciliation import *
from datetime import datetime

def run_pipeline(mode="dry-run"):
    s172 = load_phase172_state()
    s174 = load_phase174_artifacts()
    s175 = load_phase175_artifacts()
    universe = build_universe_reconciler()
    mismatch = build_candidate_mismatch_analyzer()
    task_matrix = build_task_coverage_matrix()
    artifact = build_artifact_completeness_checker()
    history = build_history_integrity_checker()
    digest = build_digest_consistency_checker()
    monitoring = build_monitoring_plan_consistency_checker()
    coverage_status = build_coverage_status_consistency_checker()
    treatment = build_rejected_deferred_treatment_validator()
    exceptions = build_exception_register()
    repair = build_repair_plan()
    guard = build_phase176_guard()
    qg = build_phase176_quality_gate()
    cc = build_phase176_cannot_conclude_guard()

    execute = mode == "execute"
    if execute:
        os.makedirs("09_runbooks/generated/phase176_reconciliation",exist_ok=True)
        result = {"reconciled":True,"timestamp":datetime.now().isoformat(),"mismatch":mismatch["phase176_candidate_mismatch_analyzer"],"repair":repair["phase176_repair_plan"]}
        with open("09_runbooks/generated/phase176_reconciliation/reconciliation_result.json","w",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2)

    mm = mismatch["phase176_candidate_mismatch_analyzer"]
    return {"phase176_reconciliation_pipeline":{
        "mode":mode,"phase":"phase176","strategy":"coverage_state_audit_and_reconciliation",
        "research_only":True,"audit_only":True,
        "coverage_state_count":s172["phase172_state"]["coverage_state_count"],
        "activated":s172["phase172_state"]["activated_count"],
        "kept":s172["phase172_state"]["kept_count"],
        "deferred":s172["phase172_state"]["deferred_count"],
        "rejected":s172["phase172_state"]["rejected_count"],
        "task_count":s175["phase175_artifacts"]["task_count"],
        "task_candidate_count":s175["phase175_artifacts"]["candidate_count"],
        "candidate_mismatch_detected":mm["mismatch_detected"],
        "candidate_mismatch_status":mm["mismatch_status"],
        "missing_candidate_ids":mm["missing_from_tasks"],
        "orphan_task_count":task_matrix["phase176_task_coverage_matrix"]["orphan_task_count"],
        "duplicate_task_count":task_matrix["phase176_task_coverage_matrix"]["duplicate_task_count"],
        "artifact_completeness":artifact["phase176_artifact_completeness"]["status"],
        "history_integrity":history["phase176_history_integrity"]["status"],
        "digest_consistency":digest["phase176_digest_consistency"]["consistency"],
        "monitoring_consistency":monitoring["phase176_monitoring_plan_consistency"]["status"],
        "exception_count":exceptions["phase176_exception_register"]["exception_count"],
        "repair_required":repair["phase176_repair_plan"]["repair_required"],
        "guard":guard["phase176_guard"]["status"],
        "quality_gate":qg["phase176_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase176_cannot_conclude_guard"]["status"],
        "violations":qg["phase176_quality_gate"]["violations"],
        "state_write_allowed":False,"owner_decision_write_allowed":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"llm_api_called":False,
        "mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase177: Deep dive packet generation for formal research coverage."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
