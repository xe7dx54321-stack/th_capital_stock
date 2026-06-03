def classify_onboarding_readiness(packets_with_judge):
    results = []
    for p in packets_with_judge:
        judge = p.get("judge_agent_review", {})
        decision = judge.get("judge_decision", "blocked_for_now")
        if decision == "ready_for_owner_approval": readiness = "owner_approval_pending"
        elif decision in ("needs_evidence_agent_follow_up", "needs_risk_agent_follow_up"): readiness = "needs_follow_up"
        elif decision in ("needs_identity_confirmation", "needs_source_route_confirmation"): readiness = "needs_manual_confirmation"
        else: readiness = "not_ready"
        results.append({"ticker": p["ticker"], "onboarding_readiness": readiness, "judge_decision": decision})
    summary = {}
    for r in results: summary[r["onboarding_readiness"]] = summary.get(r["onboarding_readiness"], 0) + 1
    return {"phase153_readiness_classifier": {"total": len(results), "summary": summary,
        "results": results, "readiness_not_equal_to_activated": True,
        "mock_used": False, "fixture_used": False}}
