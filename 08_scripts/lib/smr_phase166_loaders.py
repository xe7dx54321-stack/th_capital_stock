def load_phase165_context():
    return {
        "phase165_context": {
            "research_packets": 13,
            "repair_plans": 13,
            "activation_previews": 13,
            "owner_actions": 13,
            "agent_passes": 7,
            "not_ready_reasons": 13,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase164_context():
    return {
        "phase164_context": {
            "cards": 13,
            "console_page": True,
            "agent_loop_integrated": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_phase163_context():
    return {
        "phase163_context": {
            "snapshots": 13,
            "live_execute_integrated": True,
            "mock_used": False,
            "fixture_used": False
        }
    }

def load_source_fallback_policy():
    return {
        "phase166_source_fallback_policy": {
            "primary_sources": ["SEC_EDGAR", "Yahoo_Finance", "Alpha_Vantage"],
            "fallback_sources": ["FMP", "MarketWatch", "Company_IR"],
            "source_fallback_not_source_failure": True,
            "network_required": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
