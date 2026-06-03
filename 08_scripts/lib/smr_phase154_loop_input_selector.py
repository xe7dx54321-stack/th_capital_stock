def build_loop_input_selector(tier_assignments, onboarding_packets):
    core = [a["ticker"] for a in tier_assignments.get("assignments", []) if a["tier"] == "core"]
    watch = [a["ticker"] for a in tier_assignments.get("assignments", []) if a["tier"] == "watch"]
    candidate = [a["ticker"] for a in tier_assignments.get("assignments", []) if a["tier"] == "candidate"]
    ready = [p["ticker"] for p in (onboarding_packets or [])]
    all_targets = list(dict.fromkeys(core + watch + candidate + ready))
    return {"phase154_loop_input_selector": {
        "loop_targets_total": len(all_targets), "core_targets": core,
        "watch_targets": watch, "candidate_targets": candidate,
        "ready_for_owner_targets": ready, "all_targets": all_targets,
        "loop_targets": all_targets,
        "mock_used": False, "fixture_used": False,
    }}
