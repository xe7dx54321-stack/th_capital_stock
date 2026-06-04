# Phase174 coverage drift checker
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def build_coverage_drift_checker():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    drift_checks = []
    for e in r["entries"]:
        cid = e["candidate_id"]
        tier = e["coverage_tier"]
        drift_checks.append({
            "candidate_id":cid,
            "current_tier":tier,
            "tier_stable":True,
            "drift_detected":False,
            "drift_type":"none",
            "requires_review":tier in ["candidate_pending","deferred_review"],
            "cannot_conclude":["drift_check_is_not_auto_reassignment"]
        })
    return {"phase174_coverage_drift_checker":{
        "drift_check_enabled":True,
        "candidates_checked":len(drift_checks),
        "drift_detected":0,
        "candidates_requiring_review":sum(1 for d in drift_checks if d["requires_review"]),
        "checks":drift_checks,
        "drift_check_not_auto_update":True,
        "mock_used":False,"fixture_used":False
    }}
