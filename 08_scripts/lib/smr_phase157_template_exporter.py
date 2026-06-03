def export_decision_template(candidates):
    template = [{"ticker":c["ticker"],"decision":"pending_owner_review","rationale":"","options":["approve_research_activation","defer_to_next_review","request_more_evidence","request_identity_confirmation","request_source_route_confirmation","reject_for_now"]} for c in candidates]
    return {"phase157_template_exporter":{"template_exported":True,"candidates":len(template),"template":template,"format":"json","ready_for_owner_fill":True,"mock_used":False,"fixture_used":False}}
