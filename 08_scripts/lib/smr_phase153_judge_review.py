def build_judge_agent_review_packet(candidate, review_packets):
    checks = {"identity": review_packets.get("identity_review", {}).get("identity_status") == "verified",
              "source_route": review_packets.get("source_route_review", {}).get("source_route_ready", False),
              "financial_route": review_packets.get("financial_route_review", {}).get("financial_route_ready", False),
              "valuation_route": review_packets.get("valuation_route_review", {}).get("valuation_route_ready", False)}
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    if passed == total: decision = "ready_for_owner_approval"
    elif passed >= total - 1: decision = "needs_evidence_agent_follow_up"
    elif passed >= 2: decision = "needs_identity_confirmation"
    else: decision = "blocked_for_now"
    return {"packet_type": "judge_agent_review", "ticker": candidate["ticker"],
        "judge_checks": checks, "checks_passed": f"{passed}/{total}",
        "judge_decision": decision,
        "judge_decision_not_equal_to_investment_approval": True,
        "judge_decision_not_equal_to_watch_activation": True,
        "notes": ["All route checks passed; ready for owner review" if decision == "ready_for_owner_approval" else f"Judge decision: {decision}"],
        "cannot_conclude": ["judge_review_is_research_only", "not_investment_approval"],
        "mock_used": False, "fixture_used": False}
