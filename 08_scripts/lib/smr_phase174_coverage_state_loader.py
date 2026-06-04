# Phase174 coverage state loader
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def load_coverage_state():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    return {
        "phase174_coverage_state_loader":{
            "state_loaded":r["status"]=="state_loaded",
            "coverage_state_count":r["coverage_state_count"],
            "activated_count":r["activated_count"],
            "kept_count":r["kept_count"],
            "deferred_count":r["deferred_count"],
            "rejected_count":r["rejected_count"],
            "coverage_state_only":True,
            "trade_state_not_loaded":True,
            "state_path_ignored":True,
            "mock_used":False,"fixture_used":False
        }
    }
