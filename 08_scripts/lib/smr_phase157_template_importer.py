def import_decision_template(filled_template=None, candidates=None):
    if filled_template is None:
        decisions = []
        if candidates:
            decisions = [{"ticker":c["ticker"],"decision":"pending_owner_review","rationale":""} for c in candidates]
        return {"phase157_template_importer":{"owner_input_present":False,"decisions_imported":len(decisions),"decisions":decisions,"all_pending":True,"auto_approval_not_applied":True,"mock_used":False,"fixture_used":False}}
    return {"phase157_template_importer":{"owner_input_present":True,"decisions_imported":len(filled_template),"decisions":filled_template,"mock_used":False,"fixture_used":False}}
