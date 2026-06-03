def build_phase154_domain_registry():
    return {"phase154_domain_registry": {
        "domains": [{"domain": "multi_agent_research_loop", "description": "8-agent research loop with handoff and Judge review", "status": "active"}],
        "cross_phase_dependencies": [
            {"phase": "phase153", "dependency": "onboarding_review_packets", "usage": "load ready_for_owner_approval candidates"},
            {"phase": "phase152", "dependency": "admission_scoring", "usage": "load candidate scores"},
            {"phase": "phase150", "dependency": "tier_assignments", "usage": "load Core/Watch/Candidate tiers"},
            {"phase": "phase149", "dependency": "agent_instructions", "usage": "agent role definitions"},
            {"phase": "phase146", "dependency": "agent_memory_task_queue", "usage": "write loop results to memory/queue"},
        ],
        "mock_used": False, "fixture_used": False,
    }}
