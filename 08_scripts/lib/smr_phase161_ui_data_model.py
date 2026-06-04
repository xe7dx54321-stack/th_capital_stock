def build_example_pack_ui_model():
    return {
        "phase161_ui_data_model": {
            "example_library": {
                "total": 10,
                "valid_count": 5,
                "invalid_count": 5,
                "valid_examples": [
                    {"id": "ex001", "name": "all_pending_example", "label": "All Defer", "description": "Defer all candidates for next review."},
                    {"id": "ex002", "name": "approve_some_defer_some_example", "label": "Mixed Approve/Defer", "description": "Approve some candidates, defer others."},
                    {"id": "ex003", "name": "request_more_evidence_example", "label": "Request Evidence", "description": "Request more evidence before decision."},
                    {"id": "ex004", "name": "identity_source_confirmation_example", "label": "Confirm Identity", "description": "Confirm identity and data source."},
                    {"id": "ex005", "name": "reject_for_now_example", "label": "Reject For Now", "description": "Reject specific candidates this cycle."}
                ],
                "invalid_examples": [
                    {"id": "ex006", "name": "invalid_trade_like_example", "label": "Trade-Like (DANGER)", "danger": "buy/sell/target_price language"},
                    {"id": "ex007", "name": "duplicate_candidate_example", "label": "Duplicate Ticker", "danger": "repeated ticker entries"},
                    {"id": "ex008", "name": "unknown_candidate_example", "label": "Unknown Ticker", "danger": "ticker not in candidate pool"},
                    {"id": "ex009", "name": "missing_reason_example", "label": "Missing Rationale", "danger": "empty rationale field"},
                    {"id": "ex010", "name": "requested_tier_edge_case_example", "label": "Invalid Tier", "danger": "tier not in Core/Watch/Candidate"}
                ]
            },
            "sandbox_summary": {
                "total_safe": 45,
                "total_invalid": 6,
                "total_quarantine": 6,
                "total_execution": 0,
                "expectations_all_match": True
            },
            "phase159_status": {
                "owner_input_present": False,
                "validation_ready": True,
                "missing_input_allowed": True,
                "preview_only": True
            },
            "mock_used": False,
            "fixture_used": False
        }
    }
