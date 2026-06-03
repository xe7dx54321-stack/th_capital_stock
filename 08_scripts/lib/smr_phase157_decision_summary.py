def classify_owner_decision_summary(parsed_decisions, importer):
    has_input = importer.get("owner_input_present",False)
    decisions = parsed_decisions.get("decisions",[])
    summary = {"pending":0,"approved":0,"deferred":0,"more_evidence":0,"identity_confirmation":0,"source_confirmation":0,"rejected":0,"invalid":0}
    for d in decisions:
        dec = d.get("decision","pending_owner_review")
        if dec == "pending_owner_review": summary["pending"] += 1
        elif dec == "approve_research_activation": summary["approved"] += 1
        elif dec == "defer_to_next_review": summary["deferred"] += 1
        elif dec == "request_more_evidence": summary["more_evidence"] += 1
        elif dec == "request_identity_confirmation": summary["identity_confirmation"] += 1
        elif dec == "request_source_route_confirmation": summary["source_confirmation"] += 1
        elif dec == "reject_for_now": summary["rejected"] += 1
        else: summary["invalid"] += 1
    return {"phase157_decision_summary":{"owner_input_present":has_input,"summary":summary,"total":len(decisions),"approve_not_equal_to_buy":True,"reject_not_equal_to_sell":True,"mock_used":False,"fixture_used":False}}
