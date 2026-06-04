def build_hydration_universe():
    targets = [
        {"ticker": "MRVL", "name": "Marvell Technology Inc", "market": "US", "sector": "Semiconductors", "source": "pending_owner_review"},
        {"ticker": "AMAT", "name": "Applied Materials Inc", "market": "US", "sector": "Semiconductor Equipment", "source": "pending_owner_review"},
        {"ticker": "LRCX", "name": "Lam Research Corp", "market": "US", "sector": "Semiconductor Equipment", "source": "pending_owner_review"},
        {"ticker": "KLAC", "name": "KLA Corporation", "market": "US", "sector": "Semiconductor Equipment", "source": "pending_owner_review"},
        {"ticker": "INTC", "name": "Intel Corporation", "market": "US", "sector": "Semiconductors", "source": "pending_owner_review"},
        {"ticker": "SNPS", "name": "Synopsys Inc", "market": "US", "sector": "EDA Software", "source": "pending_owner_review"},
        {"ticker": "CDNS", "name": "Cadence Design Systems Inc", "market": "US", "sector": "EDA Software", "source": "pending_owner_review"},
        {"ticker": "CRM", "name": "Salesforce Inc", "market": "US", "sector": "Enterprise Software", "source": "pending_owner_review"},
        {"ticker": "TSM", "name": "Taiwan Semiconductor Manufacturing", "market": "US", "sector": "Semiconductors", "source": "candidate_pool"},
        {"ticker": "ASML", "name": "ASML Holding NV", "market": "US", "sector": "Semiconductor Equipment", "source": "candidate_pool"},
        {"ticker": "AMD", "name": "Advanced Micro Devices Inc", "market": "US", "sector": "Semiconductors", "source": "candidate_pool"},
        {"ticker": "SNOW", "name": "Snowflake Inc", "market": "US", "sector": "Cloud Data", "source": "candidate_pool"},
        {"ticker": "MU", "name": "Micron Technology Inc", "market": "US", "sector": "Memory Semiconductors", "source": "candidate_pool"}
    ]
    return {
        "phase162_hydration_universe": {
            "candidate_hydration_targets": len(targets),
            "minimum_targets_met": len(targets) >= 8,
            "preferred_targets_met": len(targets) >= 13,
            "markets": {"US": 13},
            "sources": {"pending_owner_review": 8, "candidate_pool": 5},
            "targets": targets,
            "mock_used": False,
            "fixture_used": False
        }
    }
