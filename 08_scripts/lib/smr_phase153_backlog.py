def build_phase153_backlog(packets_data):
    entries = []
    for p in packets_data:
        judge = p.get("review_packets", {}).get("judge_agent_review", {})
        entries.append({"ticker": p["ticker"], "name": p.get("name", ""),
                       "judge_decision": judge.get("judge_decision", ""),
                       "status": "onboarding_review_complete"})
    return {"phase153_backlog": {"entries": len(entries), "backlog": entries,
        "mock_used": False, "fixture_used": False}}
