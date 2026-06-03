def build_manual_approval_queue(eligibility_result):
    results = eligibility_result.get("results", [])
    queue = []
    for r in results:
        if r["reason"] == "owner_approval_pending":
            queue.append({"ticker": r["ticker"], "status": "awaiting_owner_approval",
                         "requires_manual_sign_off": True})
    return {"phase153_approval_queue": {"queue_size": len(queue), "approval_queue": queue,
        "auto_approval_disabled": True, "owner_approval_required": True,
        "mock_used": False, "fixture_used": False}}
