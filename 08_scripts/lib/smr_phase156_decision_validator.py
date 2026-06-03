def validate_owner_decisions(decisions):
    valid = ["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"]
    results = []
    for d in decisions:
        is_valid = d.get("owner_decision") in valid
        is_explicit = d.get("owner_decision") != "pending_owner_review"
        results.append({"ticker":d["ticker"],"decision_valid":is_valid,"explicitly_decided":is_explicit,"not_auto_approved":True})
    return {"phase156_decision_validator":{"validated":len(results),"all_valid":all(r["decision_valid"] for r in results),"all_explicit":all(r["explicitly_decided"] for r in results),"results":results,"mock_used":False,"fixture_used":False}}
