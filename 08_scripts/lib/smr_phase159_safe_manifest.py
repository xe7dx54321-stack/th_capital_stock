def build_safe_submission_manifest(normalized, quarantine):
    safe = [d for d in normalized.get("decisions",[]) if d["ticker"] not in {q["ticker"] for q in quarantine.get("quarantined",[])}]
    return {"phase159_safe_manifest":{"safe_count":len(safe),"safe_decisions":safe,"manifest_is_not_watch_update":True,"manifest_is_not_execution":True,"quarantined_count":quarantine.get("invalid_count",0),"mock_used":False,"fixture_used":False}}
