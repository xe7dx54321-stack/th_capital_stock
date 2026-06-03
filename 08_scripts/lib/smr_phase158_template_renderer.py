def render_decision_template_json(candidates):
    template = [{"ticker":c["ticker"],"decision":"pending_owner_review","rationale":"<fill your rationale here>","options":["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"]} for c in candidates]
    return {"phase158_template_renderer":{"template_json":template,"copyable":True,"auto_approval_not_applied":True,"mock_used":False,"fixture_used":False}}
