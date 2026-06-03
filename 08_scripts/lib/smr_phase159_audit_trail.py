def build_submission_audit_trail(file_locator, quarantine, safe_manifest):
    return {"phase159_audit_trail":{"input_present":file_locator.get("owner_input_present",False),"invalid_count":quarantine.get("invalid_count",0),"safe_count":safe_manifest.get("safe_count",0),"audit_path_ignored":True,"audit_not_trade_log":True,"mock_used":False,"fixture_used":False}}
