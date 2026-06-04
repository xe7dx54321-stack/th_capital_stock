def build_copy_guide():
    return {
        "phase160_copy_guide": {
            "title": "Owner Decision Copy Guide",
            "description": "How to safely copy and adapt example templates for your actual owner decision input.",
            "steps": [
                {"step": 1, "action": "Open a valid example from the example pack (ex001-ex005)."},
                {"step": 2, "action": "Copy the input_json content into your owner_decision_input.json file."},
                {"step": 3, "action": "Modify each decision entry: change ticker, decision, rationale, and requested_tier as needed."},
                {"step": 4, "action": "Ensure all tickers are in the current pending_owner_review candidate list."},
                {"step": 5, "action": "Use only allowed decisions: approve_research_activation, defer_to_next_review, reject_for_now, request_more_evidence, confirm_identity_source."},
                {"step": 6, "action": "Never include: buy, sell, target_price, position_sizing, trade, order, short, add, reduce."},
                {"step": 7, "action": "Always provide a non-empty rationale for each decision."},
                {"step": 8, "action": "Run Phase159 validation to verify your input before final submission."}
            ],
            "warnings": [
                "DO NOT copy invalid examples (ex006-ex010) as templates.",
                "DO NOT modify the real owner_decision_input.json while sandbox is running.",
                "DO NOT include trade-like language even in rationale fields.",
                "Sandbox writes to a separate file and will never overwrite your real input."
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
