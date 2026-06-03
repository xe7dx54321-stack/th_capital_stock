def build_phase153_domain_registry():
    return {"phase153_domain_registry": {
        "domains": [{"domain": "candidate_onboarding_review", "description": "Judge-gated onboarding review packets", "status": "active"}],
        "cross_phase_dependencies": [
            {"phase": "phase152", "dependency": "admission_scoring", "usage": "load admitted candidates"},
            {"phase": "phase151", "dependency": "discovery_queue", "usage": "load candidate source/trigger info"},
            {"phase": "phase150", "dependency": "tier_assignments", "usage": "check capacity"},
            {"phase": "phase149", "dependency": "agent_instructions", "usage": "route to Evidence/Risk agents"},
            {"phase": "phase148", "dependency": "activation_plans", "usage": "activation template"},
        ],
        "mock_used": False, "fixture_used": False,
    }}
