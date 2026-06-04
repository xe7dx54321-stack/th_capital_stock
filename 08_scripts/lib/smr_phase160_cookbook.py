def build_cookbook():
    return {
        "phase160_owner_decision_cookbook": {
            "title": "Owner Decision Cookbook",
            "description": "Practical recipes for common owner decision scenarios.",
            "recipes": [
                {
                    "recipe_id": "r001",
                    "scenario": "Approve one candidate for research activation to Watch tier",
                    "use_example": "ex002 (approve/defer mixed)",
                    "template": {"decisions": [{"ticker": "CANDIDATE_TICKER", "decision": "approve_research_activation", "rationale": "Your rationale here.", "requested_tier": "Watch"}]}
                },
                {
                    "recipe_id": "r002",
                    "scenario": "Defer all candidates pending more data",
                    "use_example": "ex001 (all pending)",
                    "template": {"decisions": [{"ticker": "CANDIDATE_TICKER", "decision": "defer_to_next_review", "rationale": "Your rationale here."}]}
                },
                {
                    "recipe_id": "r003",
                    "scenario": "Request additional evidence before decision",
                    "use_example": "ex003 (evidence request)",
                    "template": {"decisions": [{"ticker": "CANDIDATE_TICKER", "decision": "request_more_evidence", "rationale": "Specific evidence needed."}]}
                },
                {
                    "recipe_id": "r004",
                    "scenario": "Reject a candidate for current cycle",
                    "use_example": "ex005 (reject for now)",
                    "template": {"decisions": [{"ticker": "CANDIDATE_TICKER", "decision": "reject_for_now", "rationale": "Specific rejection reason."}]}
                },
                {
                    "recipe_id": "r005",
                    "scenario": "Confirm identity and data source before proceeding",
                    "use_example": "ex004 (identity confirmation)",
                    "template": {"decisions": [{"ticker": "CANDIDATE_TICKER", "decision": "confirm_identity_source", "rationale": "Confirmed identity and data source."}]}
                }
            ],
            "anti_patterns": [
                "Never use invalid examples (ex006-ex010) as templates.",
                "Never include trade language (buy/sell/target_price) in rationale.",
                "Never leave rationale empty.",
                "Never request invalid tiers (only Core/Watch/Candidate allowed).",
                "Never include tickers not in the pending_owner_review list."
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
