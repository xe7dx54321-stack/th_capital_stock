def build_phase157_handoff_package(safe_manifest, preview):
    return {"phase159_handoff_package":{"package_ready":True,"handoff_to":"phase157_decision_input_workflow","safe_decisions_count":safe_manifest.get("safe_count",0),"preview_count":preview.get("previews",0),"handoff_not_execution":True,"mock_used":False,"fixture_used":False}}
