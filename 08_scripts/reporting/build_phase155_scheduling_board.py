import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase155_loaders import load_phase154_loop_results
    from smr_phase155_daily_loop_plan import build_daily_loop_plan
    from smr_phase155_weekly_loop_plan import build_weekly_loop_plan
    from smr_phase155_event_trigger_plan import build_event_trigger_plan
    from smr_phase155_tier_frequency_policy import build_tier_frequency_policy
    from smr_phase155_workload_budget import run_workload_budget_enforcer
    from smr_phase155_history_writer import write_loop_run_history
    from smr_phase155_history_reader import read_loop_run_history
    from smr_phase155_delta_comparator import build_loop_delta_comparator
    from smr_phase155_stale_detector import detect_stale_loops
    from smr_phase155_missed_detector import detect_missed_loops
    from smr_phase155_degraded_handler import handle_degraded_loop
    from smr_phase155_retry_policy import build_retry_policy
    from smr_phase155_delivery_integration import build_delivery_integration
    from smr_phase155_archive_manifest import build_archive_manifest
    from smr_phase155_health_summary import build_loop_health_summary
    from smr_phase155_owner_digest import build_owner_review_digest
    from smr_phase155_next_task_scheduler import build_next_task_scheduler

    targets = load_phase154_loop_results()
    daily = build_daily_loop_plan(targets)
    weekly = build_weekly_loop_plan(targets)
    event = build_event_trigger_plan()
    tier = build_tier_frequency_policy()
    budget = run_workload_budget_enforcer(weekly["phase155_weekly_loop_plan"])
    history_w = write_loop_run_history({"run_id":"phase155-001"})
    history_r = read_loop_run_history()
    delta = build_loop_delta_comparator(history_r["phase155_history_reader"], {"targets":targets["all"]})
    stale = detect_stale_loops(history_r, targets["all"])
    missed = detect_missed_loops(history_r, weekly)
    degraded = handle_degraded_loop()
    retry = build_retry_policy()
    delivery = build_delivery_integration()
    archive = build_archive_manifest()
    health = build_loop_health_summary(history_r, stale, missed, degraded)
    digest = build_owner_review_digest(targets["all"])
    next_task = build_next_task_scheduler(targets["all"])

    return {"phase155_scheduling_board":{
        "loop_plan":{"daily":daily["phase155_daily_loop_plan"],"weekly":weekly["phase155_weekly_loop_plan"],"event":event["phase155_event_trigger_plan"],"tier_frequency":tier["phase155_tier_frequency_policy"],"workload_budget":budget["phase155_workload_budget"]},
        "loop_history":{"written":history_w["phase155_history_writer"],"reader":history_r["phase155_history_reader"],"delta":delta["phase155_delta_comparator"],"stale":stale["phase155_stale_detector"],"missed":missed["phase155_missed_detector"]},
        "loop_resilience":{"degraded":degraded["phase155_degraded_handler"],"retry":retry["phase155_retry_policy"]},
        "delivery":{"integration":delivery["phase155_delivery_integration"],"archive":archive["phase155_archive_manifest"]},
        "outputs":{"health":health["phase155_health_summary"],"owner_digest":digest["phase155_owner_digest"],"next_tasks":next_task["phase155_next_task_scheduler"]},
        "research_only":True,"agent_simulation_only":True,"watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
