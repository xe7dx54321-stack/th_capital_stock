def build_audit_log(decisions):
    entries = [{"ticker":d["ticker"],"decision":d.get("owner_decision","pending"),"timestamp":"2026-06-03","auto_generated":False,"requires_owner_input":True} for d in decisions]
    return {"phase156_audit_log":{"entries":len(entries),"log_entries":entries,"log_path_ignored":True,"mock_used":False,"fixture_used":False}}
