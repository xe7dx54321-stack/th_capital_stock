def build_example_manifest():
    return {
        "phase160_example_manifest": {
            "manifest_version": "1.0",
            "generated_for": "phase160_owner_decision_example_pack",
            "example_types": {
                "valid_safe_examples": [
                    {"example_id": "ex001", "name": "all_pending_example", "category": "valid", "risk_level": "safe"},
                    {"example_id": "ex002", "name": "approve_some_defer_some_example", "category": "valid", "risk_level": "safe"},
                    {"example_id": "ex003", "name": "request_more_evidence_example", "category": "valid", "risk_level": "safe"},
                    {"example_id": "ex004", "name": "identity_source_confirmation_example", "category": "valid", "risk_level": "safe"},
                    {"example_id": "ex005", "name": "reject_for_now_example", "category": "valid", "risk_level": "safe"}
                ],
                "invalid_dangerous_examples": [
                    {"example_id": "ex006", "name": "invalid_trade_like_example", "category": "invalid", "risk_level": "dangerous", "danger": "Contains buy/sell/target_price language"},
                    {"example_id": "ex007", "name": "duplicate_candidate_example", "category": "invalid", "risk_level": "warning", "danger": "Contains duplicate ticker entries"},
                    {"example_id": "ex008", "name": "unknown_candidate_example", "category": "invalid", "risk_level": "warning", "danger": "Contains ticker not in candidate pool"},
                    {"example_id": "ex009", "name": "missing_reason_example", "category": "invalid", "risk_level": "warning", "danger": "Contains empty rationale fields"},
                    {"example_id": "ex010", "name": "requested_tier_edge_case_example", "category": "invalid", "risk_level": "warning", "danger": "Contains invalid tier request"}
                ]
            },
            "usage_instructions": "Valid examples can be used as templates for owner decision input. Invalid examples demonstrate what will be rejected by Phase159 validation.",
            "mock_used": False,
            "fixture_used": False
        }
    }
