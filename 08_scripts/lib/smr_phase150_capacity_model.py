def build_capacity_model():
    model = {
        "max_total": 50,
        "current_utilization": 13,
        "utilization_pct": 26.0,
        "by_tier": {
            "core": {"max": 10, "current": 3, "available": 7, "coverage": "full: daily monitoring + detail pages + agent coverage + evidence chain + deep dive"},
            "watch": {"max": 20, "current": 5, "available": 15, "coverage": "standard: financial monitoring + thesis tracking + periodic review"},
            "candidate": {"max": 20, "current": 5, "available": 15, "coverage": "light: onboarding pipeline + activation planning only"},
        },
        "promotion_rules": [
            {"from_tier": "candidate", "to_tier": "watch", "conditions": ["activation_complete", "owner_approved", "source_verified", "financial_loaded"]},
            {"from_tier": "watch", "to_tier": "core", "conditions": ["deep_dive_completed", "thesis_strengthened", "evidence_chain_strong", "owner_confirmed"]},
        ],
        "demotion_rules": [
            {"from_tier": "core", "to_tier": "watch", "conditions": ["thesis_weakened", "source_degraded", "monitoring_gap"]},
            {"from_tier": "watch", "to_tier": "candidate", "conditions": ["source_blocked_long_term", "thesis_invalidated"]},
        ],
        "capacity_alerts": [
            {"condition": "core >= 8", "action": "review core tier for potential demotions"},
            {"condition": "candidate >= 15", "action": "prioritize candidate activation queue"},
        ]
    }
    return {"phase150_capacity_model": {"model": model, "mock_used": False, "fixture_used": False}}
