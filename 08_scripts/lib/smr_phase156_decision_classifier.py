def classify_owner_decisions(review_input):
    packets = review_input.get("review_packets",[])
    classified = {"pending_owner_review":0,"approved":0,"deferred":0,"more_evidence":0,"identity_confirmation":0,"source_confirmation":0,"rejected":0}
    for p in packets:
        d = p.get("owner_decision","pending_owner_review")
        if d == "pending_owner_review": classified["pending_owner_review"] += 1
        elif d == "approve_research_activation": classified["approved"] += 1
        elif d == "defer_to_next_review": classified["deferred"] += 1
        elif d == "request_more_evidence": classified["more_evidence"] += 1
        elif d == "request_identity_confirmation": classified["identity_confirmation"] += 1
        elif d == "request_source_route_confirmation": classified["source_confirmation"] += 1
        elif d == "reject_for_now": classified["rejected"] += 1
    return {"phase156_decision_classifier":{"summary":classified,"total":len(packets),"pending_is_default":True,"approve_not_equal_to_buy":True,"reject_not_equal_to_sell":True,"mock_used":False,"fixture_used":False}}
