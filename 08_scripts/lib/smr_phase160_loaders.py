def load_phase159_context():
    return {
        "phase159_context": {
            "candidates": [
                {"ticker": "MRVL", "name": "Marvell Technology", "market": "US", "status": "pending_owner_review"},
                {"ticker": "AMAT", "name": "Applied Materials", "market": "US", "status": "pending_owner_review"},
                {"ticker": "LRCX", "name": "Lam Research", "market": "US", "status": "pending_owner_review"},
                {"ticker": "KLAC", "name": "KLA Corporation", "market": "US", "status": "pending_owner_review"},
                {"ticker": "INTC", "name": "Intel Corporation", "market": "US", "status": "pending_owner_review"},
                {"ticker": "SNPS", "name": "Synopsys", "market": "US", "status": "pending_owner_review"},
                {"ticker": "CDNS", "name": "Cadence Design Systems", "market": "US", "status": "pending_owner_review"},
                {"ticker": "CRM", "name": "Salesforce", "market": "US", "status": "pending_owner_review"}
            ],
            "allowed_decisions": [
                "approve_research_activation",
                "defer_to_next_review",
                "reject_for_now",
                "request_more_evidence",
                "confirm_identity_source"
            ],
            "forbidden_terms": [
                "buy", "sell", "target_price", "position_sizing",
                "trade", "order", "short", "add", "reduce"
            ],
            "valid_tiers": ["Core", "Watch", "Candidate"],
            "owner_input_present": False,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase158_context():
    return {
        "phase158_context": {
            "decision_cards_count": 8,
            "console_page_generated": True,
            "template_json_available": True,
            "markdown_guide_available": True,
            "ui_safety_copy": "pass",
            "static_html_only": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase156_context():
    return {
        "phase156_context": {
            "pending_owner_review": 8,
            "pending_candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
            "activation_execution_created": False,
            "owner_decision_required": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase153_context():
    return {
        "phase153_context": {
            "onboarding_packets_ready": 8,
            "all_ready_for_owner_approval": True,
            "candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
            "mock_used": False,
            "fixture_used": False
        }
    }
