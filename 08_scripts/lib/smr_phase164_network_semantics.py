def resolve_network_mode_semantics(mode="dry-run"):
    semantics = {
        "dry-run": {"snapshot_data": "simulated_not_real", "agent_tasks": "not_registered", "explanation": "dry-run: no real data fetched, no Agent tasks registered. Use for preview only."},
        "execute": {"snapshot_data": "framework_ready_network_deferred", "agent_tasks": "not_registered", "explanation": "execute: snapshot framework executes but network calls deferred (execute_network_allowed=false). Agent tasks are research-only."},
        "skip-network": {"snapshot_data": "all_deferred", "agent_tasks": "not_registered", "explanation": "skip-network: all snapshots deferred. Framework validates but no data is fetched."}
    }
    s = semantics.get(mode, semantics["dry-run"])
    return {
        "phase164_network_semantics": {
            "mode": mode,
            "snapshot_data": s["snapshot_data"],
            "agent_tasks": s["agent_tasks"],
            "explanation": s["explanation"],
            "dry_run_semantics_clarified": mode == "dry-run",
            "execute_semantics_clarified": mode == "execute",
            "skip_network_semantics_clarified": mode == "skip-network",
            "mock_used": False, "fixture_used": False
        }
    }
