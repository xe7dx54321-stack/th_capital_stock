def classify_judge_decisions(packets_with_judge):
    decisions = []
    for p in packets_with_judge:
        d = p.get("judge_decision", "blocked_for_now")
        rp = p.get("review_packets", {})
        judge_rp = rp.get("judge_agent_review", {})
        decisions.append({"ticker": p["ticker"], "judge_decision": d,
                         "checks_passed": judge_rp.get("checks_passed", "0/0")})
    summary = {}
    for d in ["ready_for_owner_approval", "needs_evidence_agent_follow_up", "needs_risk_agent_follow_up",
              "needs_identity_confirmation", "needs_source_route_confirmation",
              "defer_until_better_evidence", "blocked_for_now"]:
        summary[d] = sum(1 for x in decisions if x["judge_decision"] == d)
    return {"phase153_judge_classifier": {"total": len(decisions), "summary": summary,
        "decisions": decisions, "judge_pass_not_equal_to_investment_approval": True,
        "mock_used": False, "fixture_used": False}}
