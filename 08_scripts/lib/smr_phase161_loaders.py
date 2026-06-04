def load_phase160_context():
    return {
        "phase160_context": {
            "total_examples": 10,
            "valid_examples": 5,
            "invalid_examples": 5,
            "expectations_all_match": True,
            "sandbox_total_safe": 45,
            "sandbox_total_invalid": 6,
            "sandbox_total_quarantine": 6,
            "sandbox_total_execution": 0,
            "copy_guide_available": True,
            "cookbook_available": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase159_context():
    return {
        "phase159_context": {
            "owner_input_present": False,
            "submission_validation_enabled": True,
            "validators": ["schema", "membership", "decision", "forbidden_terms", "tier", "completeness", "duplicate"],
            "safe_manifest_enabled": True,
            "quarantine_enabled": True,
            "preview_only": True,
            "activation_execution_allowed": False,
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
            "static_html_only": True,
            "execution_button_enabled": False,
            "trade_button_enabled": False,
            "form_submit_enabled": False,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase156_context():
    return {
        "phase156_context": {
            "pending_owner_review": 8,
            "candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
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
