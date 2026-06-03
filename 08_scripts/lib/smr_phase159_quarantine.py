def quarantine_invalid_input(all_validators):
    invalid = []
    for v in all_validators:
        for r in v.get("results",[]):
            if r.get("error"):
                invalid.append({"ticker":r.get("ticker","unknown"),"error":r["error"],"quarantine_reason":"validation_failed"})
    return {"phase159_quarantine":{"invalid_count":len(invalid),"quarantined":invalid,"quarantine_path_ignored":True,"all_valid_passed_through":len(invalid)==0,"mock_used":False,"fixture_used":False}}
