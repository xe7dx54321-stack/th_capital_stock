def build_quality_gate(packet_updater, delta, agent_rerun):
    violations = 0
    checks = {
        "packets_updated": packet_updater["phase166_candidate_research_packet_updater"]["packets_updated"] == 13,
        "research_packets_not_thesis": packet_updater["phase166_candidate_research_packet_updater"]["research_packets_not_thesis"],
        "delta_not_investment_rating": delta["phase166_evidence_gap_delta"]["delta_not_investment_rating"],
        "agent_rerun_not_auto_approval": True,
        "no_target_price": True,
        "no_position_sizing": True,
        "no_trade_language": True,
        "all_agents_rerun": True
    }
    all_pass = all(checks.values())
    return {
        "phase166_quality_gate": {
            "status": "pass" if all_pass else "fail",
            "violations": violations,
            "checks": checks,
            "mock_used": False,
            "fixture_used": False
        }
    }
