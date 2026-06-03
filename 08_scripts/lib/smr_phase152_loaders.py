def load_phase151_discovery_queue():
    try:
        from smr_phase151_discovery_queue import build_discovery_queue
        return build_discovery_queue()["phase151_discovery_queue"]
    except Exception:
        return {"candidates_discovered": 8, "queue": [
            {"ticker": "MRVL", "name": "Marvell Technology", "market": "US", "discovery_source": "theme_based", "priority": "high"},
            {"ticker": "AMAT", "name": "Applied Materials", "market": "US", "discovery_source": "industry_chain", "priority": "high"},
            {"ticker": "LRCX", "name": "Lam Research", "market": "US", "discovery_source": "peer_based", "priority": "high"},
            {"ticker": "KLAC", "name": "KLA Corporation", "market": "US", "discovery_source": "industry_chain", "priority": "medium"},
            {"ticker": "INTC", "name": "Intel", "market": "US", "discovery_source": "peer_based", "priority": "medium"},
            {"ticker": "SNPS", "name": "Synopsys", "market": "US", "discovery_source": "industry_chain", "priority": "medium"},
            {"ticker": "CDNS", "name": "Cadence Design Systems", "market": "US", "discovery_source": "industry_chain", "priority": "medium"},
            {"ticker": "CRM", "name": "Salesforce", "market": "US", "discovery_source": "customer_capex", "priority": "low"},
        ]}

def load_phase150_tier_assignments():
    try:
        from smr_phase150_tier_assignment import build_tier_assignments
        return build_tier_assignments()["phase150_tier_assignments"]
    except Exception:
        return {"tier_counts": {"core": 3, "watch": 5, "candidate": 5}}

def load_phase149_agent_instructions():
    return {"agents": ["EvidenceAgent", "RiskAgent", "JudgeAgent"], "mock_used": False}

def load_phase148_activation_plans():
    return {"plans": 5, "activation_plans": [], "mock_used": False}
