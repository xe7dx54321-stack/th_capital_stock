def build_research_only_evidence_fill_guard(network_guard, provenance, validator):
    violations = 0
    checks = {
        "research_only": True,
        "live_evidence_fill_not_owner_approval": True,
        "updated_packet_not_confirmed_thesis": True,
        "agent_rerun_not_factual_evidence": True,
        "readiness_delta_not_investment_rating": True,
        "activation_preview_not_execution": True,
        "owner_action_not_trade": True,
        "watch_core_updated": False,
        "candidate_auto_activated": False,
        "tier_update_executed": False,
        "target_price_found": 0,
        "position_sizing_found": 0,
        "trade_language_found": 0,
        "raw_saved": False,
        "planned_vs_live_distinction_maintained": network_guard["phase166_network_mode_semantics_guard"]["planned_evidence_is_not_live_evidence"]
    }
    return {
        "phase166_research_only_evidence_fill_guard": {
            "status": "pass" if violations == 0 else "fail",
            "violations": violations,
            "checks": checks,
            "cannot_conclude": ["guard_pass_is_not_evidence_verification", "guard_is_not_quality_approval"],
            "mock_used": False,
            "fixture_used": False
        }
    }
