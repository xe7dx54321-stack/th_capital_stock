def load_phase153_context():
    return {
        "phase153_context": {
            "onboarding_packets_ready": 8,
            "candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
            "all_ready_for_owner_approval": True,
            "mock_used": False, "fixture_used": False
        }
    }

def load_phase152_context():
    return {
        "phase152_context": {
            "admission_scored": 8,
            "all_admit_to_onboarding_review": True,
            "candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
            "mock_used": False, "fixture_used": False
        }
    }

def load_phase151_context():
    return {
        "phase151_context": {
            "auto_discovered": 8,
            "candidates": ["MRVL", "AMAT", "LRCX", "KLAC", "INTC", "SNPS", "CDNS", "CRM"],
            "mock_used": False, "fixture_used": False
        }
    }

def load_phase161_context():
    return {
        "phase161_context": {
            "ui_feedback_integrated": True,
            "owner_input_present": False,
            "example_library_available": True,
            "mock_used": False, "fixture_used": False
        }
    }

def load_source_fallback_policy():
    return {
        "phase162_source_fallback_policy": {
            "rules": [
                {"priority": 1, "source": "sec_edgar", "condition": "US-listed common stock", "requires_login": False},
                {"priority": 2, "source": "hkex_news", "condition": "HK-listed", "requires_login": False},
                {"priority": 3, "source": "sse_disclosure", "condition": "Shanghai-listed", "requires_login": False},
                {"priority": 4, "source": "szse_disclosure", "condition": "Shenzhen-listed", "requires_login": False}
            ],
            "free_sources_only": True,
            "no_login_sources_only": True,
            "mock_used": False, "fixture_used": False
        }
    }
