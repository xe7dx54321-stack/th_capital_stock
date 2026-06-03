def build_owner_decision_intake(candidates):
    templates = []
    for c in candidates:
        templates.append({"ticker":c["ticker"],"owner_decision":"pending_owner_review","rationale":"","requires_owner_input":True,"owner_decision_options":["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"],"default_is_pending_not_approved":True})
    return {"phase156_decision_intake":{"decision_templates":len(templates),"templates":templates,"owner_must_explicitly_decide":True,"no_auto_approval":True,"mock_used":False,"fixture_used":False}}
