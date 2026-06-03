def classify_activation_eligibility(readiness_result):
    results = readiness_result.get("results", [])
    eligible = []
    for r in results:
        if r["onboarding_readiness"] == "owner_approval_pending":
            eligible.append({"ticker": r["ticker"], "activation_eligible": False,
                           "reason": "owner_approval_pending", "auto_activate": False})
        else:
            eligible.append({"ticker": r["ticker"], "activation_eligible": False,
                           "reason": f"not_ready: {r['onboarding_readiness']}", "auto_activate": False})
    return {"phase153_activation_eligibility": {"total": len(eligible),
        "eligible_for_manual_approval": sum(1 for e in eligible if e["reason"] == "owner_approval_pending"),
        "auto_activated": 0, "results": eligible,
        "activation_allowed": False, "watch_core_updated": False,
        "mock_used": False, "fixture_used": False}}
