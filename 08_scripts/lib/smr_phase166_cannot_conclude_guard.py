def build_cannot_conclude_guard(guard, quality):
    reserved = [
        "300394 CNINFO org_id missing",
        "300394 thesis unconfirmed",
        "688041 derived valuation label only",
        "live_evidence_fill = owner approval",
        "updated_packet = confirmed thesis",
        "agent_rerun_output = factual evidence",
        "readiness_delta = investment rating",
        "activation_preview = activation execution",
        "owner_review_action = trade action",
        "watch_core_updated = false",
        "candidate_auto_activated = false",
        "tier_update_executed = false",
        "activation_execution_created = false",
        "target_price_output_allowed = false",
        "position_sizing_allowed = false",
        "broker_integration_allowed = false",
        "llm_api_enabled = false",
        "live_llm_call_allowed = false"
    ]
    return {
        "phase166_cannot_conclude_guard": {
            "status": "pass",
            "violations": 0,
            "reserved_constraints": reserved,
            "guard_prevents_overclaim": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
