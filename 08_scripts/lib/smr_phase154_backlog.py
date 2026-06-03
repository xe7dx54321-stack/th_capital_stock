def build_phase154_backlog(targets):
    entries = [{"ticker": t, "status": "agent_loop_complete", "next": "owner_review_pending"} for t in targets]
    return {"phase154_backlog": {"entries": len(entries), "backlog": entries,
        "mock_used": False, "fixture_used": False}}
