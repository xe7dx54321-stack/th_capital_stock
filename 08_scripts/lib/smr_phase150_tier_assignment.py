def build_tier_assignments():
    assignments = [
        {"ticker": "NVDA", "tier": "core", "reason": "Highest conviction, strengthened thesis, deep dive completed"},
        {"ticker": "AVGO", "tier": "core", "reason": "AI networking thesis supported, financial data confirmed"},
        {"ticker": "688041.SH", "tier": "core", "reason": "Semiconductor substitution thesis, financial coverage active"},
        {"ticker": "300308.SZ", "tier": "watch", "reason": "Optical demand context-supported, no direct order-book data"},
        {"ticker": "002230.SZ", "tier": "watch", "reason": "AI/software stable, limited financial differentiation"},
        {"ticker": "09988.HK", "tier": "watch", "reason": "Cloud acceleration observed, HKEX source limitation"},
        {"ticker": "00700.HK", "tier": "watch", "reason": "Gaming/ad recovery observed, HKEX source limitation"},
        {"ticker": "300394.SZ", "tier": "watch", "reason": "CNINFO org_id missing, alternative partial data, thesis unconfirmed"},
        {"ticker": "TSM", "tier": "candidate", "reason": "Pre-activation planning, not yet onboarded"},
        {"ticker": "ASML", "tier": "candidate", "reason": "Pre-activation planning, not yet onboarded"},
        {"ticker": "AMD", "tier": "candidate", "reason": "Pre-activation planning, not yet onboarded"},
        {"ticker": "SNOW", "tier": "candidate", "reason": "Pre-activation planning, not yet onboarded"},
        {"ticker": "MU", "tier": "candidate", "reason": "Pre-activation planning, not yet onboarded"},
    ]
    counts = {"core": sum(1 for a in assignments if a["tier"]=="core"), "watch": sum(1 for a in assignments if a["tier"]=="watch"), "candidate": sum(1 for a in assignments if a["tier"]=="candidate")}
    return {"phase150_tier_assignments": {"total": len(assignments), "tier_counts": counts, "assignments": assignments, "mock_used": False, "fixture_used": False}}
