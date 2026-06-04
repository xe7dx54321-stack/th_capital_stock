def build_example_schema():
    return {
        "phase160_example_schema": {
            "required_fields": [
                "example_id", "example_name", "description",
                "input_json", "expected_validation_status",
                "expected_safe_count", "expected_invalid_count",
                "expected_quarantine_count", "expected_preview_count",
                "expected_execution_count", "is_valid_example", "is_trade_like"
            ],
            "input_json_schema": {
                "decisions": "list of {ticker, decision, rationale, requested_tier(optional)}"
            },
            "allowed_decisions": [
                "approve_research_activation",
                "defer_to_next_review",
                "reject_for_now",
                "request_more_evidence",
                "confirm_identity_source"
            ],
            "forbidden_fields": [
                "buy", "sell", "target_price", "position_sizing",
                "trade", "order", "short", "add", "reduce"
            ],
            "valid_tiers": ["Core", "Watch", "Candidate"],
            "mock_used": False,
            "fixture_used": False
        }
    }
