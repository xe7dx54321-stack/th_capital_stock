def build_network_mode_semantics_guard(mode="dry-run"):
    guard = {
        "phase166_network_mode_semantics_guard": {
            "mode": mode,
            "dry_run_does_not_fetch": True,
            "execute_fetches_real_data": True,
            "skip_network_uses_cached_or_placeholder": True,
            "planned_evidence_is_not_live_evidence": True,
            "current_network_status": "no_network" if mode == "dry-run" else ("real_network" if mode == "execute" else "cached_only"),
            "evidence_actually_filled": mode == "execute",
            "cannot_conclude": [
                "planned_evidence_is_not_live_evidence",
                "dry_run_does_not_fetch_real_data",
                "network_guard_does_not_change_evidence_quality"
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
    if mode == "dry-run":
        guard["phase166_network_mode_semantics_guard"]["warning"] = "planned evidence targets only; no real data fetched"
    elif mode == "skip-network":
        guard["phase166_network_mode_semantics_guard"]["warning"] = "using cached or placeholder data; evidence may be stale"
    return guard
