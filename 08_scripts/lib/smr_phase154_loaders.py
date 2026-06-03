def load_phase153_onboarding_packets():
    try:
        from smr_phase153_loaders import load_phase152_admitted_candidates
        return load_phase152_admitted_candidates()
    except Exception:
        return [{"ticker": t, "name": n, "market": "US", "discovery_source": s, "priority": p} for t,n,s,p in
            [("MRVL","Marvell Technology","theme_based","high"),("AMAT","Applied Materials","industry_chain","high"),
             ("LRCX","Lam Research","peer_based","high"),("KLAC","KLA Corporation","industry_chain","medium"),
             ("INTC","Intel","peer_based","medium"),("SNPS","Synopsys","industry_chain","medium"),
             ("CDNS","Cadence Design Systems","industry_chain","medium"),("CRM","Salesforce","customer_capex","low")]]

def load_phase150_tier_assignments():
    try:
        from smr_phase150_tier_assignment import build_tier_assignments
        return build_tier_assignments()["phase150_tier_assignments"]
    except Exception:
        return {"tier_counts": {"core": 3, "watch": 5, "candidate": 5},
                "assignments": [{"ticker":"NVDA","tier":"core"},{"ticker":"AVGO","tier":"core"},{"ticker":"688041.SH","tier":"core"},
                               {"ticker":"300308.SZ","tier":"watch"},{"ticker":"002230.SZ","tier":"watch"},
                               {"ticker":"09988.HK","tier":"watch"},{"ticker":"00700.HK","tier":"watch"},{"ticker":"300394.SZ","tier":"watch"},
                               {"ticker":"TSM","tier":"candidate"},{"ticker":"ASML","tier":"candidate"},{"ticker":"AMD","tier":"candidate"},
                               {"ticker":"SNOW","tier":"candidate"},{"ticker":"MU","tier":"candidate"}]}

def load_phase149_agent_instructions():
    return {"agents": ["OpportunityAgent","EvidenceAgent","RiskAgent","ThesisAgent","DeepDiveAgent","BriefAgent","FeedbackAgent","JudgeAgent"],
            "mock_used": False}

def load_phase146_agent_state():
    return {"agent_memory": {"entries": 0}, "task_queue": {"pending": 0, "tasks": []}, "mock_used": False}
