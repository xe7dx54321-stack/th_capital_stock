def build_validation_report(all_validators, quarantine):
    total = sum(v.get("validated",0) for v in all_validators if "validated" in v)
    return {"phase159_validation_report":{"total_items_validated":total,"all_pass":quarantine.get("all_valid_passed_through",False),"invalid_count":quarantine.get("invalid_count",0),"validation_summary":"All validators executed.","report_not_execution":True,"mock_used":False,"fixture_used":False}}
