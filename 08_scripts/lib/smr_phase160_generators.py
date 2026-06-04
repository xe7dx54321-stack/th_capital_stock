def generate_all_pending_example():
    return {
        "example_id": "ex001",
        "example_name": "all_pending_example",
        "description": "Owner defers all 8 candidates for next review. All decisions are valid safe deferrals.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "defer_to_next_review", "rationale": "Theme fit confirmed but competitive moat analysis needs another review cycle."},
                {"ticker": "AMAT", "decision": "defer_to_next_review", "rationale": "Cyclical exposure requires more data points before activation decision."},
                {"ticker": "LRCX", "decision": "defer_to_next_review", "rationale": "Similar cyclical pattern to AMAT; needs correlated sector review."},
                {"ticker": "KLAC", "decision": "defer_to_next_review", "rationale": "Process control leader but valuation relative to peer group needs alignment."},
                {"ticker": "INTC", "decision": "defer_to_next_review", "rationale": "Turnaround thesis requires observable milestones before activation."},
                {"ticker": "SNPS", "decision": "defer_to_next_review", "rationale": "EDA duopoly strength acknowledged but regulatory risk needs monitoring."},
                {"ticker": "CDNS", "decision": "defer_to_next_review", "rationale": "Similar EDA thesis; paired review with SNPS recommended."},
                {"ticker": "CRM", "decision": "defer_to_next_review", "rationale": "Software cycle metrics need one more quarter of evidence."}
            ]
        },
        "expected_validation_status": "pass",
        "expected_safe_count": 8,
        "expected_invalid_count": 0,
        "expected_quarantine_count": 0,
        "expected_preview_count": 8,
        "expected_execution_count": 0,
        "is_valid_example": True,
        "is_trade_like": False
    }

def generate_approve_defer_mixed_example():
    return {
        "example_id": "ex002",
        "example_name": "approve_some_defer_some_example",
        "description": "Owner approves 3 candidates for research activation, defers 5. Mixed valid decisions.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Custom ASIC and data center networking thesis strongly aligns with AI infrastructure coverage. Onboarding packet confirms theme fit and financial data availability.", "requested_tier": "Watch"},
                {"ticker": "AMAT", "decision": "approve_research_activation", "rationale": "Semiconductor equipment leader with direct exposure to AI capex cycle. Validated financial data source available.", "requested_tier": "Watch"},
                {"ticker": "LRCX", "decision": "approve_research_activation", "rationale": "Etch and deposition leader complementary to AMAT coverage. Financial data confirmed.", "requested_tier": "Watch"},
                {"ticker": "KLAC", "decision": "defer_to_next_review", "rationale": "Process control metrics need validation against AMAT and LRCX before decision."},
                {"ticker": "INTC", "decision": "defer_to_next_review", "rationale": "Foundry strategy outcome still uncertain. Defer until Q2 execution evidence."},
                {"ticker": "SNPS", "decision": "defer_to_next_review", "rationale": "Regulatory review of Ansys acquisition pending. Defer until clearance."},
                {"ticker": "CDNS", "decision": "defer_to_next_review", "rationale": "Paired review with SNPS. Defer for synchronous sector evaluation."},
                {"ticker": "CRM", "decision": "defer_to_next_review", "rationale": "Agent force monetization trajectory needs one more quarter."}
            ]
        },
        "expected_validation_status": "pass",
        "expected_safe_count": 8,
        "expected_invalid_count": 0,
        "expected_quarantine_count": 0,
        "expected_preview_count": 8,
        "expected_execution_count": 0,
        "is_valid_example": True,
        "is_trade_like": False
    }

def generate_request_more_evidence_example():
    return {
        "example_id": "ex003",
        "example_name": "request_more_evidence_example",
        "description": "Owner requests additional evidence for 4 candidates before making activation decision.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "request_more_evidence", "rationale": "Need competitive moat depth analysis and customer concentration breakdown before activation decision."},
                {"ticker": "AMAT", "decision": "request_more_evidence", "rationale": "Request detailed capex cycle sensitivity analysis and foundry customer exposure breakdown."},
                {"ticker": "LRCX", "decision": "request_more_evidence", "rationale": "Need NAND/DRAM vs logic exposure split and technology transition roadmap assessment."},
                {"ticker": "KLAC", "decision": "request_more_evidence", "rationale": "Request process control market share trend data and service revenue growth trajectory."},
                {"ticker": "INTC", "decision": "defer_to_next_review", "rationale": "Defer while evidence requests for semiconductor peers are processed."},
                {"ticker": "SNPS", "decision": "defer_to_next_review", "rationale": "Regulatory timeline uncertain."},
                {"ticker": "CDNS", "decision": "defer_to_next_review", "rationale": "Paired deferral with SNPS."},
                {"ticker": "CRM", "decision": "defer_to_next_review", "rationale": "Awaiting Q1 agent force monetization data."}
            ]
        },
        "expected_validation_status": "pass",
        "expected_safe_count": 8,
        "expected_invalid_count": 0,
        "expected_quarantine_count": 0,
        "expected_preview_count": 8,
        "expected_execution_count": 0,
        "is_valid_example": True,
        "is_trade_like": False
    }

def generate_identity_source_confirmation_example():
    return {
        "example_id": "ex004",
        "example_name": "identity_source_confirmation_example",
        "description": "Owner confirms identity and data source for candidates before proceeding.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "confirm_identity_source", "rationale": "Confirmed Marvell Technology Inc. identity and SEC EDGAR as primary financial data source."},
                {"ticker": "AMAT", "decision": "confirm_identity_source", "rationale": "Confirmed Applied Materials Inc. identity and SEC filing data availability."},
                {"ticker": "LRCX", "decision": "confirm_identity_source", "rationale": "Confirmed Lam Research Corp identity and 10-K/10-Q data source validated."},
                {"ticker": "KLAC", "decision": "confirm_identity_source", "rationale": "Confirmed KLA Corp identity and annual report data access confirmed."},
                {"ticker": "INTC", "decision": "confirm_identity_source", "rationale": "Confirmed Intel Corp identity. Note: turnaround phase requires quarterly monitoring frequency."},
                {"ticker": "SNPS", "decision": "confirm_identity_source", "rationale": "Confirmed Synopsys Inc identity and EDGAR data availability."},
                {"ticker": "CDNS", "decision": "confirm_identity_source", "rationale": "Confirmed Cadence Design Systems identity and filing data confirmed."},
                {"ticker": "CRM", "decision": "confirm_identity_source", "rationale": "Confirmed Salesforce Inc identity and SEC data source validated."}
            ]
        },
        "expected_validation_status": "pass",
        "expected_safe_count": 8,
        "expected_invalid_count": 0,
        "expected_quarantine_count": 0,
        "expected_preview_count": 8,
        "expected_execution_count": 0,
        "is_valid_example": True,
        "is_trade_like": False
    }

def generate_reject_for_now_example():
    return {
        "example_id": "ex005",
        "example_name": "reject_for_now_example",
        "description": "Owner rejects 2 candidates for current review cycle due to unresolved concerns.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Custom silicon thesis alignment strong.", "requested_tier": "Watch"},
                {"ticker": "AMAT", "decision": "approve_research_activation", "rationale": "Equipment cycle thesis validated.", "requested_tier": "Watch"},
                {"ticker": "LRCX", "decision": "defer_to_next_review", "rationale": "Defer for paired equipment sector review."},
                {"ticker": "KLAC", "decision": "defer_to_next_review", "rationale": "Defer for process control sector alignment."},
                {"ticker": "INTC", "decision": "reject_for_now", "rationale": "Turnaround thesis has insufficient observable milestones. Reject for current cycle; may revisit after Q3 execution data."},
                {"ticker": "SNPS", "decision": "reject_for_now", "rationale": "Ansys acquisition regulatory risk unresolved. Reject for current cycle; revisit after clearance."},
                {"ticker": "CDNS", "decision": "defer_to_next_review", "rationale": "Paired deferral with SNPS rejection."},
                {"ticker": "CRM", "decision": "defer_to_next_review", "rationale": "Agent force data pending."}
            ]
        },
        "expected_validation_status": "pass",
        "expected_safe_count": 8,
        "expected_invalid_count": 0,
        "expected_quarantine_count": 0,
        "expected_preview_count": 8,
        "expected_execution_count": 0,
        "is_valid_example": True,
        "is_trade_like": False
    }

def generate_invalid_trade_like_example():
    return {
        "example_id": "ex006",
        "example_name": "invalid_trade_like_example",
        "description": "Owner input contains trade-like language (buy, target_price). This MUST be quarantined.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Buy this stock now. Target price 120. Strong buy signal."},
                {"ticker": "NVDA", "decision": "approve_research_activation", "rationale": "Add to Core position. This is a trade order."}
            ]
        },
        "expected_validation_status": "fail",
        "expected_safe_count": 0,
        "expected_invalid_count": 2,
        "expected_quarantine_count": 2,
        "expected_preview_count": 0,
        "expected_execution_count": 0,
        "is_valid_example": False,
        "is_trade_like": True
    }

def generate_duplicate_candidate_example():
    return {
        "example_id": "ex007",
        "example_name": "duplicate_candidate_example",
        "description": "Input contains duplicate ticker entries. Duplicate checker should flag this.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Strong AI infrastructure theme alignment.", "requested_tier": "Watch"},
                {"ticker": "MRVL", "decision": "defer_to_next_review", "rationale": "Conflicting second entry for same ticker."},
                {"ticker": "AMAT", "decision": "defer_to_next_review", "rationale": "Defer for sector review."}
            ]
        },
        "expected_safe_count": 2,
        "expected_invalid_count": 1,
"expected_quarantine_count": 1,
        "expected_preview_count": 2,
        "expected_execution_count": 0,
        "is_valid_example": False,
        "is_trade_like": False
    }

def generate_unknown_candidate_example():
    return {
        "example_id": "ex008",
        "example_name": "unknown_candidate_example",
        "description": "Input contains ticker not in candidate pool. Membership validator should flag.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Valid candidate.", "requested_tier": "Watch"},
                {"ticker": "AAPL", "decision": "approve_research_activation", "rationale": "Not in current candidate pool. Unknown ticker."}
            ]
        },
        "expected_validation_status": "fail",
        "expected_safe_count": 1,
        "expected_invalid_count": 1,
        "expected_quarantine_count": 1,
        "expected_preview_count": 1,
        "expected_execution_count": 0,
        "is_valid_example": False,
        "is_trade_like": False
    }

def generate_missing_reason_example():
    return {
        "example_id": "ex009",
        "example_name": "missing_reason_example",
        "description": "Input has empty rationale field. Completeness checker should flag.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "", "requested_tier": "Watch"},
                {"ticker": "AMAT", "decision": "defer_to_next_review", "rationale": "Valid rationale present."}
            ]
        },
        "expected_validation_status": "fail",
        "expected_safe_count": 1,
        "expected_invalid_count": 1,
        "expected_quarantine_count": 1,
        "expected_preview_count": 1,
        "expected_execution_count": 0,
        "is_valid_example": False,
        "is_trade_like": False
    }

def generate_requested_tier_edge_example():
    return {
        "example_id": "ex010",
        "example_name": "requested_tier_edge_case_example",
        "description": "Input requests invalid tier. Tier validator should flag.",
        "input_json": {
            "decisions": [
                {"ticker": "MRVL", "decision": "approve_research_activation", "rationale": "Valid rationale.", "requested_tier": "Portfolio"},
                {"ticker": "AMAT", "decision": "approve_research_activation", "rationale": "Valid rationale.", "requested_tier": "Watch"}
            ]
        },
        "expected_validation_status": "fail",
        "expected_safe_count": 1,
        "expected_invalid_count": 1,
        "expected_quarantine_count": 1,
        "expected_preview_count": 1,
        "expected_execution_count": 0,
        "is_valid_example": False,
        "is_trade_like": False
    }

def generate_all_examples():
    return {
        "phase160_example_pack": {
            "total_examples": 10,
            "valid_examples": 5,
            "invalid_examples": 5,
            "examples": [
                generate_all_pending_example(),
                generate_approve_defer_mixed_example(),
                generate_request_more_evidence_example(),
                generate_identity_source_confirmation_example(),
                generate_reject_for_now_example(),
                generate_invalid_trade_like_example(),
                generate_duplicate_candidate_example(),
                generate_unknown_candidate_example(),
                generate_missing_reason_example(),
                generate_requested_tier_edge_example()
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
